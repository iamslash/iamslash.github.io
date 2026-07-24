# 부하 조절과 내구성, 그리고 POC 너머

이 글은 "대용량 메시지 처리 도구: Erlang 에서 Elixir 까지" 9부작 시리즈의 마지막 글이다. 바로 앞 8편에서는 대화 코어를 `ChatBot.Conversation` GenServer 로 만들고, Registry 와 DynamicSupervisor 로 대화당 프로세스를 관리하며, `ChatBot.TaskSupervisor` 로 동시 LLM 호출을 격리하고, Req 의 SSE 스트리밍으로 토큰을 흘려보내는 데까지 왔다. 프로토타입은 이제 "메시지를 받아 대화 프로세스로 라우팅하고 LLM 응답을 스트리밍한다"는 골격을 갖췄다. 하지만 아직 두 조각이 비어 있다. 부하가 몰릴 때 시스템이 스스로를 지키는 법(부하 조절)과, 노드가 죽어도 받은 메시지를 잃지 않는 법(내구성)이다. 이번 글에서 그 두 조각을 채운 뒤, "POC 너머 — 대용량으로 가는 길"에서 6편에 미뤄뒀던 질문, 즉 "그럼 Kafka 랑 Scylla 는 언제 쓰냐"에 답하고 시리즈를 마무리한다.

## 1부. 부하 조절 — backpressure 는 공짜가 아니라 설계다

### GenStage/Broadway — demand-driven backpressure

부하 조절의 출발점은 backpressure 다. 소비자가 감당할 수 있는 속도보다 생산자가 빠르면, 그 초과분을 어디에 쌓을 것인가. 대부분의 런타임에서 이건 직접 큐와 세마포어로 조립해야 하는 문제지만, BEAM 생태계에서는 **GenStage** 가 이를 1급 개념으로 준다. GenStage 의 핵심은 소비자가 "지금 N개까지 받을 수 있다"고 **수요(demand)** 를 위로 흘려보내고, 생산자는 그 수요만큼만 내려보낸다는 것이다. 소비자가 느려지면 수요가 줄고, 수요가 줄면 생산자가 알아서 멈춘다. 밀어내기(push)가 아니라 당겨오기(pull)라서, 흐름 제어가 파이프라인 구조에 내장된다.

실무에서 GenStage 를 직접 쓰는 대신 대개 그 위에 얹힌 **Broadway** 를 쓴다. Broadway 는 데이터 수집 파이프라인을 선언적으로 기술하게 해주고, 배치·동시성·재시도·rate limiting 을 옵션으로 제공한다. 인바운드 파이프라인을 아주 단순화하면 이런 모양이다.

```elixir
defmodule ChatBot.InboundPipeline do
  use Broadway

  def start_link(_opts) do
    Broadway.start_link(__MODULE__,
      name: __MODULE__,
      producer: [
        # 프로듀서는 인바운드 소스(큐/브로커)라고 생각하면 된다.
        # 뒤에서 다룰 BroadwayKafka 가 실제 프로덕션 프로듀서의 예다.
        module: {ChatBot.InboundProducer, []},
        # 파이프라인 전체에 초당 처리량 상한을 건다.
        rate_limiting: [allowed_messages: 100, interval: 1_000]
      ],
      processors: [default: [concurrency: 50]]
    )
  end

  @impl true
  def handle_message(_processor, message, _context) do
    # message.data 를 정규화해 ChatBot.Router 로 넘긴다.
    ChatBot.Router.route(message.data)
    message
  end
end
```

여기서 `rate_limiting: [allowed_messages: 100, interval: 1_000]` 한 줄이 "1초에 최대 100건까지만 파이프라인으로 들여보낸다"는 의미다. 초과분은 프로듀서 단에서 대기하고, 이 대기가 곧 위로 전파되는 backpressure 가 된다. 다만 이 demand 가 어디까지 거슬러 올라가는지는 소스의 성격에 달렸다. Kafka 처럼 우리가 **직접 당겨오는(pull) 소스**에는 "천천히 달라"는 신호가 그대로 전파되지만, 웹훅을 쏘는 **외부 sender 에게는 자동으로 전파되지 않는다.** 외부에서 밀어넣는 트래픽은 우선 durable 큐(뒤에서 볼 Oban 같은)에 받아 두고 demand 만큼 당겨오거나, 과부하일 때 명시적으로 거절해야 backpressure 가 실제로 성립한다.

### 함정: unbounded mailbox

그런데 여기서 이 시리즈의 정직한 원칙대로 짚어야 할 함정이 있다. **BEAM 이 backpressure 를 공짜로 주지는 않는다는 것이다.** GenServer 하나를 놓고 보자. GenServer 의 메일박스는 무제한(unbounded)이다. `GenServer.cast/2` 나 그냥 `send/2` 로 메시지를 처리 속도보다 빠르게 밀어넣으면, 메일박스는 아무 저항 없이 무한히 커진다. 프로세스는 죽지 않고 멀쩡히 살아 있지만, 밀린 메시지가 힙에 쌓이면서 메모리를 먹어 치우다가 결국 노드 전체가 OOM 으로 쓰러진다. 게다가 메일박스가 길어지면 selective receive 비용도 커져서 처리가 더 느려지고, 그래서 더 밀리는 악순환에 빠진다.

핵심은 이거다. GenStage/Broadway 가 backpressure 를 "1급으로 준다"는 말은, **그 도구를 썼을 때** 흐름 제어가 구조에 내장된다는 뜻이지, 아무 GenServer 에나 메시지를 던져도 알아서 조절된다는 뜻이 아니다. `cast` 는 fire-and-forget 이라 backpressure 가 아예 없다. `call` 은 호출자를 응답 때까지 기다리게 하니 한 걸음 낫지만, 이것만으로 충분하다고 오해하면 안 된다 — `call` 은 그 **개별 호출자 하나**만 붙잡을 뿐, 동시에 `call` 하는 호출자 수 자체를 제한하지 않으면 대상 프로세스는 여전히 밀려드는 요청에 과부하될 수 있다. 실제로 backpressure 를 세우려면 **경계 있는(bounded) 큐와 제한된 워커 수**가 필요하다. 설계자는 "이 경로에 흐름 제어가 있는가"를 의식적으로 물어야 한다. backpressure 는 런타임이 거저 주는 선물이 아니라 설계 결정이다.

### 외부 LLM rate limit — 런타임은 이걸 모른다

GenStage 의 backpressure 는 **BEAM 내부** 경계에서만 작동한다. 하지만 우리 챗봇의 진짜 병목은 밖에 있다. LLM 프로바이더는 분당 토큰 수(TPM)와 분당 요청 수(RPM)에 한도를 걸어두고, 그걸 넘으면 429 를 돌려준다. BEAM 스케줄러는 이 외부 한도를 알 도리가 없다. 대화 프로세스 5만 개가 동시에 응답을 생성해도 BEAM 은 태연하게 5만 건을 전부 프로바이더로 쏘고, 프로바이더는 그중 대부분을 거절한다.

그래서 애플리케이션 레벨의 rate limiter 가 필요하다. `ChatBot.RateLimiter` 는 **Hammer**(예제는 7.x 기준)로 프로바이더의 RPM/TPM 을 우리 쪽에서 먼저 지킨다. 한 가지 버전 주의가 있다. 흔히 보이는 `Hammer.check_rate/3` 는 **구버전 API** 다. **Hammer 7 부터는 리미터 모듈을 직접 정의해 `hit/3`(또는 `hit/4`)를 쓰며, 기본 알고리즘도 토큰버킷이 아니라 fixed window** 다. 또 아래 예제의 첫 함수는 요청을 1건씩만 세므로 **RPM 만 제한할 뿐 TPM 은 제한하지 못한다.** TPM 까지 지키려면 두 번째 함수처럼 "예상 input + 허용 output" 토큰 합을 별도 token-budget 키의 증가분(increment)으로 반영해야 한다.

```elixir
defmodule ChatBot.RateLimiter do
  @moduledoc "프로바이더의 RPM/TPM 한도를 넘지 않도록 요청을 조절한다."

  # Hammer 7: 리미터 모듈을 정의하고 hit/3(·/4)로 카운트한다.
  # 기본 알고리즘은 토큰버킷이 아니라 fixed window 다.
  use Hammer, backend: :ets

  # RPM: 60초 창(window)에서 프로바이더당 요청 50건까지 허용(요청 1건씩 증가).
  def check_request(provider) do
    case hit("llm:req:#{provider}", 60_000, 50) do
      {:allow, _count} -> :ok
      {:deny, _retry_after_ms} -> {:error, :rate_limited}
    end
  end

  # TPM: 같은 창에 "예상 input + 허용 output" 토큰 합을 증가분으로 반영한다.
  # 요청 1건이 아니라 estimated_tokens 만큼 버킷을 소모하는 게 핵심이다.
  def check_tokens(provider, estimated_tokens, limit \\ 200_000) do
    case hit("llm:tok:#{provider}", 60_000, limit, estimated_tokens) do
      {:allow, _count} -> :ok
      {:deny, _retry_after_ms} -> {:error, :rate_limited}
    end
  end
end
```

LLM 을 호출하기 직전에 `ChatBot.RateLimiter.check_request(provider)` 로 RPM 을, `check_tokens(provider, 예상_토큰)` 으로 TPM 을 함께 물어보고, 둘 중 하나라도 `{:error, :rate_limited}` 면 호출을 미루거나(짧은 백오프 후 재시도) 사용자에게 잠시 기다려 달라고 알린다. 한도를 프로바이더에게 배우지 말고 우리가 먼저 지키는 것이다.

한 가지 단서를 달아야 한다. Hammer 의 기본 백엔드는 ETS 라서 이 카운터는 **노드 로컬**이다. 노드 3대로 이뤄진 클러스터라면 각 노드가 독립적으로 50건을 세므로 전역 한도는 사실상 150건이 된다. 클러스터 전역 rate limit 이 필요하면 카운터를 공유 상태로 옮겨야 한다 — Redis 백엔드를 쓰거나, 토큰 분배를 전담하는 조율 프로세스(single writer)를 두는 식이다. 프로토타입 단계에서는 노드 로컬로 충분하지만, 스케일아웃 시점에 반드시 다시 마주치는 문제다.

### 서킷브레이커와 재시도

rate limit 이 "얼마나 자주 부를까"의 문제라면, 서킷브레이커는 "상대가 아플 때 그만 부르기"의 문제다. 프로바이더가 장애에 빠져 계속 5xx 를 돌려주는데도 우리가 재시도를 반복하면, 이미 넘어진 상대를 더 밟는 꼴이고 우리 리소스도 재시도에 묶인다. `:fuse` 라이브러리로 서킷브레이커를 건다.

```elixir
# 애플리케이션 시작 시 퓨즈를 설치한다.
# 10초 안에 5번 "녹으면(melt)" 회로를 열고, 30초 후 다시 시도해 본다.
:fuse.install(:llm, {{:standard, 5, 10_000}, {:reset, 30_000}})

def call_llm(conversation_id, history, text) do
  case :fuse.ask(:llm, :sync) do
    :ok ->
      case ChatBot.LLM.stream_reply(conversation_id, history, text) do
        {:error, _reason} = err ->
          :fuse.melt(:llm)   # 실패 1회 적립 — 임계치를 넘으면 회로가 열린다
          err

        ok ->
          ok
      end

    :blown ->
      # 회로가 열려 있으면 프로바이더를 아예 호출하지 않고 빠르게 실패한다.
      {:error, :circuit_open}
  end
end
```

`:fuse.ask(:llm, :sync)` 가 회로 상태를 묻고, 실패할 때마다 `:fuse.melt(:llm)` 으로 실패를 적립한다. 임계치를 넘으면 `ask` 가 `:blown` 을 돌려주고, 그때부터는 프로바이더를 건드리지 않고 곧바로 실패시켜 시스템이 숨 돌릴 시간을 준다.

여기서 한 가지 전제를 분명히 해야 한다. 위 코드가 `{:error, _reason}` 을 melt 신호로 삼으려면, 그 앞단의 `ChatBot.LLM` 이 오류를 실제로 그 형태로 돌려줘야 한다. 그런데 8편에서 쓴 `Req.post!` 는 HTTP 4xx·5xx 를 예외가 아니라 그냥 응답(Response)으로 돌려주고, 연결 실패 같은 transport 오류는 오히려 raise 한다. 즉 상태 코드만 보고 있으면 429·500 이 `{:error, _}` 로 잡히지 않고, 네트워크 예외는 이 `case` 문을 그냥 뚫고 나간다. 그래서 LLM client 는 **non-2xx 응답·SSE 스트림 오류·transport 예외를 모두 `{:error, reason}` 하나로 정규화한 다음** 퓨즈를 melt 해야 한다.

재시도도 조심해서 얹는다. 재시도를 걸 때는 **지수 백오프**(exponential backoff — 재시도 간격을 실패할 때마다 배로 늘려 상대에게 회복할 틈을 준다)와 **지터**(jitter — 여러 client 의 재시도가 같은 순간에 몰리지 않도록 대기 시간에 작은 무작위값을 더한다)를 함께 쓴다. 다만 Req 의 기본 재시도(`:safe_transient`)는 멱등한 **GET/HEAD 에만** 적용되고 POST 스트리밍은 자동 재시도하지 않는데, 이건 버그가 아니라 안전장치다. 응답 토큰이 이미 흘러나오기 시작한 POST 를 무턱대고 재시도하면 partial 응답이 중복되고 **중복 과금**까지 생길 수 있기 때문이다. 그래서 재시도는 **응답이 시작되기 전의 안전한 오류에만** 명시적으로 건다. 이렇게 하면 (안전 범위의) 일시적 오류에는 자동 재시도를, 지속적 오류에는 서킷브레이커를 두는 2단 방어가 된다.

## 2부. 내구성 — BEAM 메시지는 노드가 죽으면 사라진다

### 핵심 논지

지금까지 이 시리즈는 fanout(팬아웃)을 BEAM 프로세스와 메시지 패싱으로 풀 수 있다고 계속 이야기했다. 여기서 반드시 못 박아야 할 사실이 있다. **BEAM 의 메시지는 휘발성이다.** 프로세스 메일박스도, 프로세스 상태도, 전부 메모리에 있다. 노드가 죽으면 그 순간 메일박스에 밀려 있던 메시지도, 처리 중이던 대화 상태도 함께 증발한다. 감독 트리가 프로세스를 재시작해 주지만, 재시작된 프로세스는 죽기 직전에 받았던 그 메시지를 다시 받지 못한다. fanout 을 BEAM 으로 대체했다고 해서 **내구성이 공짜로 따라오는 게 아니다.** 동시성·격리·감독은 BEAM 이 훌륭히 주지만, 내구성은 그것들과 별개의 축이다.

이 지점은 오해하기 쉽다. "Erlang 은 nine nines 가동률 아니냐"는 말과 "메시지가 유실될 수 있다"는 말은 모순처럼 들린다. 하지만 높은 가동률은 "시스템이 계속 살아 있다"는 뜻이지 "받은 데이터가 디스크에 안전하게 남는다"는 뜻이 아니다. 개별 노드는 언제든 죽을 수 있고, 죽으면 그 노드의 휘발성 상태는 사라진다. 내구성은 명시적으로 설계해야 한다.

### 챗봇 규모의 답: BEAM = fanout, Oban(Postgres) = durability

그럼 무엇으로 내구성을 확보할까. 여기가 사람들이 반사적으로 "Kafka!"를 외치는 지점이다. 하지만 채팅 봇 프로토타입 규모에서 답은 훨씬 소박하다. **우리는 이미 PostgreSQL 을 쓰고 있고, PostgreSQL 은 그 자체로 내구성 있는 저장소다.** 필요한 건 "인바운드 메시지를 처리하기 전에 먼저 디스크에 영속화한다"는 규율이고, 그걸 깔끔하게 해주는 도구가 **Oban** 이다. Oban 은 Postgres 를 백엔드로 쓰는 잡 큐라서, 잡을 인큐하는 순간 그 잡은 트랜잭션과 함께 테이블에 커밋된다.

채널 어댑터(7편)는 이제 인바운드 메시지를 곧바로 `ChatBot.Router` 로 넘기는 대신, **먼저 Oban 잡으로 인큐**한다.

```elixir
# 채널 어댑터/웹훅 컨트롤러: 받은 메시지를 즉시 Postgres 에 영속화한다.
%{
  "channel" => "telegram",
  "channel_user_id" => channel_user_id,
  "text" => text,
  "thread_key" => thread_key
}
|> ChatBot.Jobs.Inbound.new()
|> Oban.insert()
```

`Oban.insert/1` 이 반환된 순간, 이 메시지는 이미 Postgres 의 `oban_jobs` 테이블에 커밋되어 있다. 실제 처리는 Oban worker 가 맡는다.

```elixir
defmodule ChatBot.Jobs.Inbound do
  # max_attempts: 5 = 최초 1회 + 추가 재시도 4회 = 합 5회.
  use Oban.Worker, queue: :inbound, max_attempts: 5

  alias ChatBot.{InboundMessage, Router}

  @impl Oban.Worker
  def perform(%Oban.Job{args: args}) do
    msg = %InboundMessage{
      provider_event_id: args["provider_event_id"],
      channel: args["channel"],
      channel_user_id: args["channel_user_id"],
      text: args["text"],
      thread_key: args["thread_key"]
    }

    # end-to-end 내구성의 핵심: 라우팅에 넘기기 전에 인바운드를 먼저
    # DB 에 커밋한다. provider 가 준 event id 에 unique 제약을 걸어,
    # 재시도로 같은 잡이 다시 돌아도 두 번 저장되지 않게(idempotent) 만든다.
    # 이 커밋이 "접수됨"의 진짜 근거다 — Router.route/1 은 결국
    # GenServer.cast 라 즉시 반환할 뿐, 대화가 실제로 처리했다는 보장이 아니다.
    with {:ok, _persisted} <- InboundMessage.upsert(msg, on_conflict: :nothing) do
      Router.route(msg)
      :ok
    end
  end
end
```

`perform/1` 안에서 무슨 일이 벌어지든 — 라우팅 중 크래시가 나든, 노드가 통째로 죽든 — 잡 자체는 Postgres 에 남아 있다. 노드가 되살아나면 Oban 이 아직 끝나지 않은 잡을 집어 다시 실행한다. 여기서 정확히 짚어야 할 세 가지가 있고, 이걸 얼버무리면 "유실 없음"이라는 과장이 된다.

첫째, `max_attempts: 5` 는 **최초 1회 + 추가 재시도 4회 = 합 5회**라는 뜻이다. 다섯 번을 다 쓰고도 실패하면 잡은 재시도를 멈추고 `discarded` 상태로 남는다 — 조용히 사라지는 게 아니라 "실패로 확정된 채 보관"되는 것이라, 이 discarded 잡을 알림으로 잡아내 수동으로 복구하는 운영 장치가 필요하다.

둘째, Oban 이 보장하는 건 exactly-once 가 아니라 **at-least-once** 다. 같은 잡이 두 번 이상 실행될 수 있다(예: 처리는 끝났는데 완료 표시 직전에 노드가 죽는 경우). 그래서 위 worker 처럼 provider event id 에 unique 제약을 걸어 **중복을 무시(idempotent)** 하는 설계가 짝으로 따라와야 한다. "재시도 가능"과 "중복 없음"은 공짜로 함께 오지 않는다.

셋째, 노드가 잡을 **실행하던 도중** 죽으면 그 잡은 DB 상에 `executing` 으로 걸린 채 남아 아무도 다시 집어 가지 않는 고아(orphan)가 될 수 있다. 이런 잡을 되살리려면 **Oban Lifeline**(Pro 의 유사 기능 포함)을 설정해, executing 인 채 멈춘 잡을 다시 available 로 돌려놔야 한다.

이 세 가지를 갖추면, 크래시가 곧 데이터 유실이 되던 경로가 **재시도 가능한(durable · at-least-once) 경로**로 바뀐다.

정리하면 역할 분담은 이렇게 갈린다. **durable 하게 받는 것은 Oban/Postgres, 휘발성으로 빠르게 분배하는 것은 BEAM.** 인바운드 경계에서 한 번 디스크에 안전하게 착지시킨 다음, 그 안쪽의 fanout·동시성·스트리밍은 BEAM 의 빠르고 휘발적인 메시지 패싱에 맡긴다. 각자 잘하는 일을 시키는 것이고, 이 조합이 챗봇 프로토타입 규모에서 Kafka 없이도 **DB 에 접수된 작업을 재시도 가능한 durable at-least-once 파이프라인**으로 만든다(중복 방지는 provider event id unique 제약 + idempotent worker 가 담당한다).

## 3부. POC 너머 — 대용량으로 가는 길

프로토타입은 완성됐다. 이제 "그다음"을 이야기할 차례다. 규모가 커질 때 어디가 먼저 아프고, 그때 무엇을 꺼내 드는가.

### CPU-bound 오프로드 스펙트럼

5편에서 정직하게 인정한 Elixir 의 별표 중 하나가 CPU-bound 연산이었다. BEAM 은 수많은 동시 작업을 스케줄링하는 데는 탁월하지만, 무거운 수치 계산 한 덩어리를 빠르게 갈아 넣는 데는 네이티브 언어를 못 따라간다. 이때 오프로드의 선택지는 하나가 아니라 **스펙트럼**이다. 흔히 "가장 빠르니 NIF 부터"라고들 하지만, 속도는 **안전 기준이 아니다.** 선택 순서는 속도가 아니라 **작업이 얼마나 오래 걸리는가**와 **얼마나 강한 장애 격리가 필요한가**로 정해야 한다.

- **Rustler NIF (in-process)**: **NIF**(Native Implemented Function — 같은 VM 안에서 직접 호출되는 네이티브 함수)로 Rust 코드를 BEAM 프로세스 안에서 부른다. 프로세스 경계를 넘지 않아 오버헤드가 가장 작지만 대가가 크다 — 일반 NIF 는 실행 중 스케줄러를 **막아(block)** 다른 프로세스를 굶기거나, 크래시하면 BEAM 노드 **전체를 함께 데려갈** 수 있다. 그래서 일반 NIF 는 **짧고 충분히 검증된 계산에만** 쓴다. 계산이 길면 스케줄러를 양보하는 **dirty CPU NIF** 나 중간중간 끊어 실행하는 yielding NIF 를 쓰고, 그래도 위험하면 아래의 Port·별도 서비스로 내린다. Discord 가 정렬 같은 핫스팟을 Rust NIF 로 내려 큰 성능 이득을 본 사례가 유명하다.
- **Port (로컬 서브프로세스)**: **Port**(BEAM 과 stdin/stdout 으로 통신하는 별도 OS 프로세스)로 외부 프로그램을 띄운다. 서브프로세스가 죽어도 BEAM 은 멀쩡하니 **장애 격리가 회복된다.** 대신 프로세스 경계를 넘는 직렬화 비용이 붙는다. 긴 CPU 작업이나 장애 격리가 중요한 경우에 적합하다.
- **로컬 sidecar/gRPC**: **sidecar**(같은 머신·같은 배포 단위에 함께 띄우는 보조 서비스)를 올리고 **gRPC**(서비스 간 원격 호출을 위한 규약)로 부른다. 언어 선택이 자유롭고 배포도 분리되지만 네트워크 스택을 한 겹 통과한다.
- **원격 마이크로서비스**: 완전히 분리된 서비스로 빼낸다. 가장 유연하지만 가장 무겁다 — 네트워크 지연, 배포, 관측, 장애 모드가 전부 새로 생긴다.

다시 말하지만 이 목록의 순서는 "무조건 위에서부터"가 아니라 **작업 시간과 격리 요구에 맞춰** 고르라는 뜻이다. 짧고 검증된 계산이면 위쪽(NIF)이 맞고, 길거나 장애 격리가 중요하면 주저 없이 아래쪽(Port·서비스)으로 내려야 한다. 다만 그 반대 방향의 낭비 — 정말로 NIF 로 충분한 짧은 계산을 굳이 원격 마이크로서비스로 빼는 것 — 도 함께 경계한다. 그리고 만약 그 CPU 작업이 머신러닝 추론이라면 언어 분리조차 피할 수 있다 — **Nx/Bumblebee** 로 Elixir 안에서 텐서 연산과 모델 추론을 직접 돌릴 수 있기 때문이다.

무엇보다, 우리 LLM 챗봇에서는 이 CPU 약점 자체가 대부분 무력화된다는 점을 상기하자. 무거운 추론은 이미 **외부 API** 뒤에 있다. 우리 노드가 하는 일은 I/O 대기와 오케스트레이션 — 정확히 BEAM 이 가장 잘하는 일이다. CPU-bound 라는 별표는 이 워크로드에서는 거의 각주로 줄어든다.

### hub-and-spoke: 복잡성은 서비스 개수가 아니라 분산 상태에서 온다

CPU 작업을 밖으로 빼기 시작하면 곧 "이거 마이크로서비스 아니냐, 그 고통을 다시 떠안는 거 아니냐"는 걱정이 든다. 여기서 토폴로지를 잘 잡으면 그 고통의 대부분을 피할 수 있다. 권장 구조는 **hub-and-spoke** 다. Elixir 코어가 허브로서 **상태를 소유한 오케스트레이터**가 되고, CPU 서비스들은 스포크로서 **무상태(stateless) 순수 워커**가 된다. 워커는 입력을 받아 계산하고 결과를 돌려줄 뿐, 세션도 상태도 갖지 않는다.

이 구분이 중요한 이유는 이렇다. 마이크로서비스의 진짜 고통은 서비스 **개수**에서 오지 않는다. **분산된 상태** — 여러 서비스가 각자 상태를 들고 서로 일관성을 맞춰야 하는 상황 — 에서 온다. 분산 트랜잭션, 캐시 무효화, 순서 보장, 부분 실패 복구 같은 난제들이 전부 여기서 나온다. 워커를 무상태로 유지하면 이 난제들이 애초에 생기지 않는다. 상태는 허브(Elixir + Postgres) 한 곳에만 있고, 스포크는 언제 죽었다 살아나도 상관없는 순수 함수처럼 다뤄진다.

이건 Fred Brooks 의 **우발적 복잡성(accidental complexity) 대 본질적 복잡성(essential complexity)** 구분과 정확히 맞닿는다. LLM 추론을 밖에서 부르는 건 본질적 복잡성이다 — 그건 문제 자체에 내재한다. 반면 여러 서비스에 상태를 흩뿌려 놓고 그 일관성과 씨름하는 건 대체로 우발적 복잡성이다 — 우리가 토폴로지를 잘못 골라 스스로 만들어 낸 고통이다. 무상태 스포크는 후자를 걷어낸다.

### Kafka 와 Scylla 가 실제로 값을 하는 지점

이제 6편에서 미뤄뒀던 질문에 정면으로 답한다. **Kafka 와 Scylla 는 대체 언제 쓰는가.**

먼저 분명히 하자. 지금까지 봤듯 fanout 은 BEAM 이, 내구성은 Oban/Postgres 가 감당했다. 프로토타입은 이 둘만으로 완성된다. 그러니 Kafka/Scylla 는 "BEAM 이 못 하는 걸 메우는" 도구가 아니라, **특정 대용량 요구가 실제로 생겼을 때 그 seam(이음매)을 따라 도입하는** 도구다.

**Kafka 가 값을 하는 지점**은 그것이 단순한 큐가 아니라 **내구성 있는 리플레이 가능한 이벤트 로그**이기 때문이다. 그래서 대용량이라는 이유만이 아니라, 아래 요구 **중 하나 이상이 핵심일 때** 검토할 값을 한다(셋이 다 겹쳐야 하는 건 아니다). (1) 이벤트를 며칠씩 보관하며 새 컨슈머가 과거를 처음부터 다시 읽어야 할 때(리플레이), (2) 하나의 이벤트 스트림을 여러 독립 컨슈머 그룹이 각자의 속도로 팬아웃해 소비해야 할 때, (3) 여러 팀·여러 서비스가 언어에 상관없이 같은 이벤트 백본을 공유해야 할 때(크로스서비스). Oban 잡 큐는 (1)(2)(3) 어느 것도 목표로 하지 않는다 — 그건 "이 잡을 한 번 실행"하기 위한 것이다. Elixir 에서 Kafka 를 붙일 때는 `brod` 클라이언트를 직접 쓰거나, 앞서 본 Broadway 위에 **BroadwayKafka** 프로듀서를 얹어 backpressure 와 함께 소비한다.

**Scylla(또는 Cassandra)가 값을 하는 지점**은 흔히 "쓰기가 너무 많을 때"로 뭉뚱그려지지만, 실제 판단 기준은 단순한 write 임계치 하나가 아니다. 다음이 함께 맞을 때 값을 한다. (1) PostgreSQL 의 쓰기·수평 확장 **병목이 실측**되고, (2) 접근 패턴이 **partition key 중심의 안정적인 query**(예: 대화 ID + 시간 범위로 히스토리 조회)로 수렴하며, (3) 수평 확장을 얻는 대가로 **약한 consistency 와 늘어난 운영 비용**을 수용할 수 있을 때. 채팅 히스토리가 대표 후보인 이유는 초당 쓰기량뿐 아니라 이 query 패턴이 마침 partition 친화적이기 때문이다. Discord 가 메시지 저장소를 Cassandra 로, 다시 Scylla 로 옮긴 사례가 바로 이 지점이다. Elixir 에서는 `Xandra` 클라이언트로 접속한다. 중요한 건 **순서**다 — Postgres 로 시작해서 위 조건이 실제로 확인될 때 히스토리 저장소만 떼어 Scylla 로 옮기는 것이지, 처음부터 Scylla 를 까는 게 아니다.

바로 이 지점이 이 시리즈에서 프로토타입(6·7·8편)과 대용량(9편)을 가르는 전환점이고, 독자가 애초에 품었을 "Kafka? Scylla?"라는 질문에 대한 답이다. **둘 다 훌륭한 도구지만, BEAM 이 못 해서 쓰는 게 아니라 대용량이 실제로 문제가 됐을 때 그 문제의 이음매를 따라 도입한다.**

마지막으로 관측성 한 줄. 이 모든 조절·재시도·오프로드가 실제로 어떻게 동작하는지 보려면 계측이 필요하다. Elixir 는 `Telemetry` 이벤트를 표준으로 삼고, `PromEx` 로 Prometheus 에 메트릭을 노출하며, `Phoenix.LiveDashboard` 로 프로세스·메일박스·잡 큐 상태를 실시간으로 들여다볼 수 있다. 부하 조절의 임계값도, Scylla 로 옮길 시점도, 결국 이 숫자들이 알려준다.

## 시리즈를 마치며

아홉 편을 관통한 이야기는 결국 하나의 문장으로 접힌다. **동시성·격리성·감독성이라는 세 축이 Erlang 을 통신 산업에서 성공시켰고, 현대의 도구들은 그 세 축을 각자의 방식으로 — 언어 런타임, 타입 시스템, 라이브러리, 인프라 오케스트레이터를 조립해 — 좇아왔으며, Elixir 는 그것을 하나의 런타임 안에서 통합해 제공한다.** 다만 이 결론에는 우리가 시종일관 정직하게 달아 온 별표가 붙는다. 동시성이라는 축에서는 Go 와 Java(Loom)가 막상막하이고, Elixir 에는 CPU-bound·팀·생태계라는 현실적 약점이 있다. 이 별표를 지우지 않는 것이 이 시리즈의 논조였다. BEAM 의 강점은 허수아비를 세워야 빛나는 종류의 것이 아니라, 정직하게 저울질했을 때 격리성과 감독성에서 진짜 차이로 드러나는 종류의 것이기 때문이다.

그리고 그 통합은 추상적인 자랑이 아니라 실제로 손에 잡히는 결과였다. 3막에서 우리는 **Elixir 와 PostgreSQL 만으로 멀티채널 LLM 챗봇 게이트웨이의 프로토타입을 끝까지 완성했다.** 채널 어댑터로 여러 메신저를 하나의 정규화된 인바운드로 모으고, 대화당 프로세스로 상태를 격리하고, Task 로 동시 호출을 감독하고, SSE 로 토큰을 스트리밍하고, 이번 글에서 Hammer·`:fuse` 로 부하를 조절하고 Oban/Postgres 로 내구성을 채웠다. Kafka 도 Scylla 도 없이. 그것들은 대용량이 실제로 문제가 될 때, 리플레이 가능한 이벤트 로그가 정말 필요할 때, 채팅 히스토리의 쓰기가 정말 단일 RDBMS 를 넘어설 때, 바로 그 이음매를 따라 도입하면 된다.

이 시리즈가 남기고 싶은 마지막 감각은 이것이다. 도구는 문제의 형태를 따라 고르는 것이다. 수많은 동시적·장수명·상태 있는 연결을 soft-realtime 으로, 높은 가동률로 다뤄야 하는 문제 — 30여 년 전 전화 교환기가 마주쳤고 오늘의 메신저와 LLM 챗봇이 그대로 물려받은 그 문제 — 앞에서, BEAM 의 설계는 여전히 놀랍도록 잘 들어맞는다. 그 사실을 과장 없이, 그러나 축소 없이 전하는 것이 아홉 편 내내의 목표였다. 여기까지 함께 읽어 준 독자에게 감사를 전한다.
