# 시스템 디자인: 멀티채널 LLM 챗봇

이 시리즈의 여섯 번째 글이다. 앞선 다섯 편(막1·2)에서 우리는 BEAM 이 왜 통신 산업에서 태어났고, 동시성·격리성·감독성이라는 세 축에서 무엇을 주는지, 그리고 그 세 축을 Elixir 라는 현대적 언어로 어떻게 쓰는지를 살펴봤다. 이번 글부터는 막3(POC)이다. 이론을 접고, 실제로 돌아가는 시스템 하나를 Elixir + PostgreSQL 만으로 설계한다. 이 글은 전체 아키텍처를 그리는 청사진이고, 구현 세부(어댑터·대화 코어·부하 조절)는 7·8·9편에서 채운다.

## 스코어카드 회수: 세 축을 하나의 런타임에서

1편에서 소개하고 2·3·4편에서 채운 관통 스코어카드를 다시 꺼내자.

| 특성 | Erlang/BEAM | Go | Java (Loom) | C++ |
|---|---|---|---|---|
| 동시성 | ✅ 수백만 프로세스 | ✅ goroutine | ✅ 가상 스레드 | ⚠️ OS 스레드 한계 |
| 격리성 | ✅ share-nothing | ❌ 공유 메모리 | ❌ 공유 메모리 | ❌ 공유 메모리 |
| 감독성 | ✅ OTP 감독 트리 | 직접 구현 | 직접 구현(Akka 별도) | 직접 구현 |

핵심 서사는 이랬다. **동시성만 보면 Go 고루틴과 Java 가상 스레드가 BEAM 과 막상막하다.** 이건 정직하게 인정해야 한다. 진짜 차이는 격리성과 감독성에서 벌어진다 — 프로세스별 힙으로 크래시가 번지지 않고, OTP 감독 트리가 재시작을 언어 차원에서 보장한다.

그런데 여기서 조용히 지나치기 쉬운 사실이 하나 있다. 다른 언어들은 이 세 축을 **각각 다른 도구를 조립해서** 얻는다. 동시성은 런타임, 감독은 쿠버네티스, 상태 공유는 Redis, 이벤트 fan-out 은 또 별도 브로커. BEAM 은 이 셋을 **하나의 런타임 안에서** 준다.

> **용어 — fan-out**: 이벤트 하나를 여러 수신자에게 동시에 뿌리는 것. 막3의 목표는 바로 이 문장을 실제 시스템으로 증명하는 것이다. "세 축을 한 런타임에서 다 주는 게 BEAM 이었다. 이제 Elixir + PostgreSQL 로 그걸 진짜 시스템에 적용한다."

## POC 정의: 멀티채널 LLM 챗봇 게이트웨이

우리가 만들 것은 **멀티채널 LLM 챗봇 게이트웨이**다. 시나리오는 단순하다.

1. 사용자가 iMessage, Slack, Discord 같은 채널로 봇에게 말을 건다.
2. 게이트웨이가 그 메시지를 받아 LLM API 를 호출한다.
3. LLM 이 뱉는 토큰을 실시간으로 스트리밍해서 사용자 채널로 되돌려 보낸다.

프로토타입 단계에서는 붙이기 쉬운 Telegram 을 기본 채널로 시작하고, 이후 iMessage → Slack → Discord 로 채널을 늘려 간다. 중요한 건 **채널이 늘어나도 코어는 그대로**여야 한다는 점이다. 이게 첫 번째 설계 결정으로 이어진다.

### 요구사항

이 시스템이 실제로 감당해야 하는 것들을 나열하면 이렇다.

- **고동시·장수명 연결**: 수천~수만 명이 동시에 대화 중이고, 각 대화는 몇 분에서 몇 시간까지 살아 있다.
- **대화별 상태/컨텍스트**: 각 대화는 자기만의 히스토리를 기억한다. LLM 호출에 직전 맥락을 함께 실어 보내야 한다.
- **스트리밍 응답**: LLM 이 완성된 답을 다 만들 때까지 기다리지 않고, 토큰이 나오는 대로 흘려보낸다.
- **프로바이더 rate limit 준수**: LLM API 는 분당 요청/토큰 한도가 있다. 이걸 넘기면 429 로 차단된다.
- **재시도/failover**: 일시적 실패는 재시도하고, 한 프로바이더가 죽으면 우회한다.
- **백프레셔(backpressure)**: 인바운드가 처리 능력을 넘어서면 시스템이 무너지는 대신 속도를 늦춘다.
- **유실 방지(내구성)**: 프로세스가 크래시해도 받은 메시지를 잃지 않는다.
- **관측성**: 무슨 일이 벌어지는지 로그·메트릭·트레이스로 볼 수 있다.

> **용어 두 가지**
> - **failover**: 주 provider 가 실패하면 다른 provider 로 우회해 계속 서비스하는 것.
> - **backpressure(배압)**: 소비자가 밀리기 시작하면 생산 쪽 속도를 낮춰 시스템이 무너지지 않게 하는 흐름 제어.

## 핵심 설계 결정 두 가지

### 결정 1: 대화 하나 = 프로세스 하나

전통적인 웹 백엔드라면 이렇게 짤 것이다. 요청이 들어오면 stateless 핸들러가 Redis 에서 대화 상태를 꺼내 역직렬화하고, LLM 을 호출하고, 갱신된 상태를 다시 직렬화해 Redis 에 밀어 넣는다. 상태는 죽어 있는 바이트 뭉치로 외부 저장소에 얹혀 있고, 매 요청마다 꺼냈다 넣었다 한다.

우리는 반대로 간다. **대화 하나를 살아있는 프로세스(GenServer) 하나로** 표현한다. 대화의 히스토리와 컨텍스트는 그 프로세스의 메모리 안에 그냥 들어 있다. 직렬화도, 캐시 무효화도 없다. 대화가 시작되면 프로세스가 뜨고, 유휴 상태가 길어지면 프로세스가 스스로 종료해 메모리를 반납한다.

이걸 관리하는 도구가 `Registry` 와 `DynamicSupervisor` 다.

```elixir
defmodule ChatBot.Conversation do
  # restart: :transient — 유휴 시 스스로 {:stop, :normal, state} 로 끝내면 재시작하지 않고,
  # 예기치 못한 크래시(:normal 이 아닌 종료)만 재시작한다. 기본값 :permanent 는 정상 종료도
  # 되살려서 "유휴 시 스스로 종료"와 모순되므로 :transient 를 명시한다.
  use GenServer, restart: :transient

  # conversation_id 로 프로세스를 찾거나 없으면 띄운다.
  defp ensure_started(conversation_id) do
    case Registry.lookup(ChatBot.ConversationRegistry, conversation_id) do
      [{pid, _}] -> pid
      [] ->
        case DynamicSupervisor.start_child(
               ChatBot.ConversationSupervisor,
               {__MODULE__, conversation_id}
             ) do
          {:ok, pid} -> pid
          {:error, {:already_started, pid}} -> pid  # 다른 요청이 먼저 시작함(경쟁 조건) — 그 pid 재사용
        end
    end
  end

  # 상태(history)는 프로세스 안에 산다 — 외부 캐시가 아니라.
  @impl true
  def init(conversation_id) do
    history = ChatBot.Message.recent(conversation_id)
    {:ok, %{id: conversation_id, history: history}}
  end
end
```

`Registry` 는 `conversation_id → pid` 매핑을 들고, `DynamicSupervisor` 는 런타임에 프로세스를 동적으로 띄운다. 재시작 정책은 위 코드의 `restart: :transient` 가 정한다 — 유휴 대화가 스스로 `{:stop, :normal, state}` 로 끝내면 되살리지 않고, 예기치 못한 크래시만 재시작한다. 대화가 100만 개면 프로세스도 100만 개 — 2편에서 봤듯 BEAM 은 이만한 프로세스 수를 **감당할 수 있다**. 다만 이건 가능성이지 보장이 아니다. 실제 상한은 프로세스 개수만이 아니라 각 대화의 history 크기, mailbox 적체, node 메모리, 그리고 그 뒤의 DB·LLM capacity 에 함께 달려 있다. 그래서 실무에선 유휴 대화를 일정 시간 뒤 종료(idle eviction)해 메모리를 회수하고, 실제 목표 규모로 부하 테스트를 돌려 한계를 실측한다. (구현 전체는 8편.)

### 결정 2: 채널 어댑터를 코어에서 분리

두 번째 결정은 **코어가 채널을 몰라야 한다**는 것이다. iMessage 냐 Slack 이냐 Discord 냐는 대화 로직과 아무 상관이 없다. 그래서 채널을 behaviour 뒤로 숨긴다.

```elixir
defmodule ChatBot.Channel do
  @moduledoc "채널 어댑터 behaviour. Telegram/LinQ/Slack/Discord 가 각각 구현한다."

  @callback send_message(channel_user_id :: String.t(), text :: String.t()) ::
              :ok | {:error, term()}
end
```

각 채널 어댑터는 자기 채널의 웹훅/소켓에서 원시 메시지를 받아 **하나의 정규화된 구조체**로 바꿔 코어에 넘긴다.

```elixir
defmodule ChatBot.InboundMessage do
  @enforce_keys [:channel, :channel_user_id, :text]
  defstruct [:channel, :channel_user_id, :text, :thread_key]
end
```

> **`channel_user_id` 는 발신자 신원이다.** 이 필드는 "누가 보냈나"(Telegram 의 `from.id`)를 담는다. 응답을 **어디로** 보낼지는 발신자와 다를 수 있다 — 그룹 대화에선 목적지가 개인이 아니라 방(`chat.id`)이다. 이 POC 는 1:1 대화를 가정해 발신자와 목적지를 같게 두지만, 그룹을 지원하려면 reply 목적지를 InboundMessage 에 따로 실어야 한다(자세한 건 07편).

코어의 진입점인 `ChatBot.Router` 는 이 구조체만 알면 된다. 채널이 무엇이었는지는 `channel` 필드에 문자열로 담겨 있을 뿐, 라우팅 로직은 채널 종류에 분기하지 않는다.

```elixir
defmodule ChatBot.Router do
  alias ChatBot.{InboundMessage, Identity, Conversation}

  def route(%InboundMessage{} = msg) do
    conversation = Identity.resolve_conversation(msg)   # 신원 매핑 → 대화 찾기/생성
    Conversation.handle_user_message(conversation.id, msg.text)
  end
end
```

효과는 분명하다. **채널을 추가한다 = 어댑터 모듈 하나를 추가한다.** 코어는 한 줄도 바뀌지 않는다. (어댑터·신원 매핑 전체는 7편.)

## 아키텍처 다이어그램

두 결정을 합치면 전체 그림은 이렇게 된다.

```text
  [iMessage/LinQ]   [Slack]   [Discord]   [Telegram]
        │              │          │            │
        └──────────────┴─────┬────┴────────────┘
                             │   각 채널 어댑터가 ChatBot.Channel 구현
                             ▼
                   %ChatBot.InboundMessage{}   ← 정규화된 인바운드
                             │
                             ▼
                      ChatBot.Router ───────▶ ChatBot.Identity
                             │                 (신원 해석: 채널 유저 → 대화)
                             ▼
              Registry(ChatBot.ConversationRegistry) 로 조회
              DynamicSupervisor(ChatBot.ConversationSupervisor) 로 기동
                             │
                             ▼
        ┌───────────────────────────────────────────┐
        │  ChatBot.Conversation (GenServer)          │  대화 1개 = 프로세스 1개
        │  상태: history, context                    │
        └──────────────────┬────────────────────────┘
                           │ cast {:user_message, text}
                           ▼
             Task.Supervisor(ChatBot.TaskSupervisor)     요청마다 격리된 Task
                           │
                           ▼
             ChatBot.LLM (Req + SSE 스트리밍)
                           │  POST https://api.anthropic.com/v1/messages
                           ▼  토큰 스트림
             채널 어댑터.send_message/2 로 응답 전송

  ─────────────────────── 영속/내구성 옆단 ───────────────────────
   ChatBot.Repo ──▶ PostgreSQL : users, user_identities,
                                 conversations, messages
   Oban(ChatBot.Jobs.Inbound) ──▶ 같은 PostgreSQL (잡 큐)
```

왼쪽 위에서 흘러 들어온 메시지가 정규화 → 라우팅 → 대화 프로세스 → 격리된 Task → LLM 스트리밍 → 채널 응답으로 관통한다. 오른쪽/아래에는 PostgreSQL 이 있고, Ecto(`ChatBot.Repo`)로 영속 데이터를, Oban 으로 영속 잡 큐를 같은 데이터베이스 위에 얹는다.

## BEAM 이 흡수하는 것 vs 여전히 필요한 것

이 아키텍처에서 흥미로운 점은 **다른 스택이라면 별도 인프라를 붙였을 자리 상당수를 BEAM 내장 기능이 흡수한다**는 것이다. 다만 "흡수한다"를 "Redis 를 완전히 대체한다"처럼 읽으면 안 된다. 아래 표의 각 행은 서로 **다른 보장**을 주는 도구들이고, 이 single-node POC 의 좁은 범위 안에서만 그 자리를 대신할 뿐이다. 두 표로 정리한다.

**이 single-node POC 에서 별도로 배포하지 않는 컴포넌트**

| 보통 따로 배포하는 것 | 이 POC 에서 그 자리를 맡는 것 | 무엇에 한정되나(제한) |
|---|---|---|
| WebSocket 게이트웨이(별도 서비스) | Phoenix Channels | node 프로세스로 소켓을 들 뿐, LB·TLS 종단은 여전히 앞단이 필요 |
| Redis 세션 | GenServer + PostgreSQL | active state 만 memory 에 두고, source of truth 는 DB. node 가 죽으면 memory 상태는 사라지고 DB 에서 복원 |
| Redis 캐시 | ETS | node-local·volatile cache 에 한함(노드 재시작 시 소멸, 노드 간 공유 없음) |
| Presence 서비스 | Phoenix Presence | 연결된 cluster 안의 presence 추적에 한함 |
| Redis/NATS pub/sub | Phoenix.PubSub | 연결된 cluster 의 transient fan-out 에 한함(디스크에 남지 않음, 리플레이 불가) |
| 인트라노드 큐/백프레셔(브로커) | GenStage / Broadway | node 내부 demand 기반 배압에 한함 |
| process lifecycle/restart(pod 재기동) | OTP Supervisor | node 내부 process 복구에 한함 |
| durable background job/retry(K8s Job) | Oban + PostgreSQL | job 상태·재시도·완료를 DB 에 기록. **K8s Job 에 가까운 durable 컴포넌트는 Supervisor 가 아니라 Oban 이다** |

> **용어 — CRDT**: Conflict-free Replicated Data Type. 여러 node 가 각자 독립적으로 갱신해도 나중에 충돌 없이 하나로 자동 병합되는 데이터 구조. `Phoenix.Presence` 가 이걸로 cluster 전체의 접속 상태를 합친다.

주의: process lifecycle/restart(Supervisor)와 durable background job(Oban)을 한 줄로 묶지 않았다. Supervisor 는 **node 안에서 살아있는 process 를 되살리는** 것이고, 그 process 가 들고 있던 상태나 "해야 할 일"이 node 재시작·크래시를 넘어 **남아야** 한다면 그건 DB 에 기록하는 Oban 의 몫이다. 둘은 서로 다른 보장이다.

**여전히 필요한 것**

| 필요 | 도구 | 이유 / 언제 |
|---|---|---|
| 영속 저장 | PostgreSQL (Ecto) | BEAM 상태는 휘발성. 진짜 저장은 DB |
| 영속 잡 큐 | Oban | 재시작·재시도가 살아남는 큐는 DB 위에 |
| 내구성 이벤트 로그 | Kafka | **독립 consumer 가 과거 event 를 각자 offset 으로 replay** 해야 하거나 대용량 크로스서비스 스트림이 필요할 때. 이 POC 엔 그 요구가 없어 생략 |
| 채팅 히스토리 초고처리량 | ScyllaDB | **PostgreSQL 병목이 실측되고**, conversation 같은 안정적 partition key 가 있고, 수평 확장이 필요하며, consistency/운영 trade-off 를 수용할 때 |

핵심은 표의 경계선이다. **fan-out·상태·배압·감독 같은 "노드/클러스터 안에서 벌어지는 일"은 BEAM 이 흡수**하고, **영속·내구성·크로스서비스 로그처럼 "런타임 밖에서 살아남아야 하는 일"은 여전히 외부 시스템**이 맡는다.

## 왜 프로토타입에선 Kafka/Scylla 를 안 쓰나

여기서 가장 오해받기 쉬운 지점을 짚자. "챗봇이면 메시지 브로커(Kafka) 부터 깔아야 하는 거 아냐?" 라는 반사다. 프로토타입에서는 아니다. 이유는 **"메시지 전달"이라는 말이 두 가지 완전히 다른 것을 가리키기 때문**이다.

**첫째, BEAM 프로세스 메시지 패싱은 Kafka 가 아니다.** BEAM 의 `send`/`receive`, 그리고 `Phoenix.PubSub` 브로드캐스트는 **휘발성 인클러스터 fan-out** 이다. "지금 살아있는 프로세스들에게 이 이벤트를 뿌린다"는 것이지, 디스크에 남기거나 나중에 리플레이하는 게 아니다. Kafka 는 정반대 물건이다 — **내구성 있는 append-only 로그**로, 이벤트를 디스크에 남기고, 여러 컨슈머가 각자 offset 으로 리플레이하며, 서비스 경계를 넘어 흐른다.

> **용어 두 가지**
> - **append-only log**: 기존 내용을 지우거나 고치지 않고 **뒤에만 계속 덧붙이는** 로그. 과거 기록이 그대로 남아 나중에 다시 읽을 수 있다.
> - **offset**: consumer 가 그 로그를 **어디까지 읽었는지** 가리키는 위치. consumer 마다 자기 offset 을 들고 있어서, 서로 독립적으로 과거부터 replay 할 수 있다.

Kafka 의 값어치는 **대용량**뿐 아니라, **서로 독립인 consumer 여럿이 과거 event 를 각자 offset 으로 replay** 해야 할 때 나온다. 이 POC 에는 그런 요구(과거 스트림 재생, 크로스서비스 소비)가 없어서 생략한다. 프로토타입의 인클러스터 fan-out 에 Kafka 를 끼우는 건 망치로 압정을 박는 격이다.

**둘째, fan-out ≠ durability.** 그럼 유실 방지는 누가 하나? BEAM 으로 fan-out 을 대체하되, **유실 방지(내구성)는 Oban/PostgreSQL 이 맡는다.** 다만 여기서 정확히 짚어야 할 게 있다. **Oban 은 at-least-once 다 — exactly-once(정확히 한 번)가 아니다.** 그래서 안전하게 쓰려면 네 가지가 필요하다.

1. webhook 컨트롤러는 provider 가 준 **event id 를 idempotency key** 로 삼아 Oban 잡에 insert(commit)한 뒤에야 2xx 를 반환한다. (DB 커밋이 끝나기 전에 성공을 알리지 않는다.)
2. 실제 `Router.route` 와 처리는 컨트롤러가 아니라 **worker** 가 수행한다.
3. worker 는 **재실행돼도 결과가 한 번만 반영되도록 idempotent** 하게 짠다(같은 event id 는 한 번만 처리). at-least-once 라 재시도 시 같은 잡이 두 번 돌 수 있기 때문이다.
4. node 가 잡을 executing 하던 중에 죽으면 그 잡은 orphan 으로 남는데, 이걸 되살리려면 **Oban Lifeline** 설정이 필요하다.

즉 "휘발성 fan-out(BEAM) + 내구성 큐(Oban/Postgres)" 조합이 주는 건 "Kafka 없이도 유실 없음"이 아니라 정확히는 **durable at-least-once(재시도 가능, idempotency 로 중복을 흡수)** 다.

ScyllaDB(또는 Cassandra) 도 같은 논리다. 채팅 히스토리를 처음부터 초고처리량 분산 저장소에 넣을 이유가 없다. **PostgreSQL 로 시작한다.** Scylla 로의 이동 조건은 단순한 write 수치가 아니라, ① PostgreSQL 병목이 실제로 **실측**되고, ② conversation 처럼 안정적인 partition key 가 있으며, ③ 수평 확장이 필요하고, ④ 그 대가인 consistency·운영 복잡도 trade-off 를 수용할 때다. 프로토타입에서 이 이동은 일어나지 않는다.

이 판단 — "언제 BEAM 내장으로 충분하고, 언제 Kafka/Scylla 로 넘어가야 하는가" — 이 바로 9편(POC 너머)의 전환점이다. 지금은 이 한 줄만 붙잡으면 된다. **fan-out 은 BEAM 이, 내구성은 Oban/Postgres 가(at-least-once + idempotency). Kafka/Scylla 는 규모·리플레이 요구가 그것을 명확히 요구할 때.**

## Ecto 스키마 소개

마지막으로 "런타임 밖에서 살아남아야 하는" 영속 데이터의 모양을 정하자. 규약 스키마를 그대로 쓴다. 네 개의 테이블이면 프로토타입에 충분하다.

```sql
-- 봇을 쓰는 사람. 채널과 무관한 논리적 신원.
users(id, inserted_at)

-- 채널별 신원 매핑. 한 사람이 Slack·Discord 여러 채널을 가질 수 있다.
user_identities(id, user_id → users.id, channel, channel_user_id)

-- 대화 세션. 채널 + thread_key 로 구분.
conversations(id, user_id → users.id, channel, thread_key, inserted_at)

-- 대화 안의 개별 메시지. role 은 "user" | "assistant".
messages(id, conversation_id → conversations.id, role, content, inserted_at)
```

설계의 요점은 `users` 와 `user_identities` 의 분리다. Slack 의 `U123` 과 Discord 의 `987654` 가 **같은 사람**일 수 있다. `user_identities` 가 `(channel, channel_user_id) → user_id` 매핑을 들고, 코어는 채널 신원이 아니라 논리적 `user_id` 로만 사람을 다룬다. 이 매핑 해석이 `ChatBot.Identity.resolve_conversation/1` 이 하는 일이고, 어댑터 패턴과 나란히 "코어가 채널을 모른다"는 원칙을 데이터 층에서도 지킨다.

이렇게 살아있는 프로세스(대화 상태)와 영속 테이블(진짜 저장)의 역할을 갈라 두면, GenServer 는 뜨거운 상태를 빠르게 들고, PostgreSQL 은 차가운 진실을 안전하게 보관한다. 다음 편부터 이 뼈대에 살을 붙인다.

---

다음 글: [채널 게이트웨이: 어댑터 패턴](07-channel-gateway.md)
