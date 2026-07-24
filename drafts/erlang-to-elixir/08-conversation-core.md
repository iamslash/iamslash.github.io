# 대화 코어: GenServer 상태와 LLM 스트리밍

이 글은 "대용량 메시지 처리 도구: Erlang 에서 Elixir 까지" 9부작 시리즈의 여덟 번째 글이다. 앞선 7편에서는 채널 게이트웨이 — 어댑터 behaviour(`ChatBot.Channel`), 정규화된 인바운드 메시지(`ChatBot.InboundMessage`), 그리고 채널마다 다른 사용자를 하나의 신원으로 묶는 매핑 — 를 다뤘다. 거기서 라우터(`ChatBot.Router`)는 어떤 채널에서 온 메시지든 결국 하나의 진입점, 즉 대화 프로세스로 흘려보냈다. 이번 글에서는 바로 그 진입점, POC 의 심장인 **대화 코어**를 만든다. 대화 하나당 프로세스 하나로 상태를 관리하고, 그 안에서 LLM API 를 동시에 호출하며, 응답 토큰을 실시간으로 스트리밍한다. 1막과 2막에서 개념으로만 이야기했던 동시성·격리성·감독성이 실제 LLM 워크로드 위에서 어떻게 코드가 되는지, 여기서 처음으로 온전히 드러난다.

## 대화당 GenServer

핵심 설계 결정은 단순하다. **대화 하나 = 프로세스 하나.** 사용자가 봇과 나누는 각각의 대화를 독립적인 `ChatBot.Conversation` GenServer 프로세스에 대응시킨다. 통화 하나에 프로세스 하나, 웹소켓 연결 하나에 프로세스 하나 — 3편에서 본 그 패턴을 이번엔 "대화 하나에 프로세스 하나"로 그대로 가져온 것이다.

문제는 라우터가 특정 대화의 프로세스를 어떻게 찾느냐다. `conversation_id`(정수/문자열)는 알고 있지만, 그에 해당하는 pid 는 런타임에 동적으로 정해진다. (pid = 실행 중인 process 의 주소표. 이 값이 있어야 특정 프로세스에 메시지를 보낼 수 있다.) 이걸 이어주는 것이 **Registry** 다. `ChatBot.ConversationRegistry` 에 `conversation_id → pid` 매핑을 등록해 두고, 라우터는 id 로 pid 를 조회한다. 프로세스가 아직 없으면 `DynamicSupervisor`(`ChatBot.ConversationSupervisor`)로 그 자리에서 시작한다.

```elixir
defmodule ChatBot.Conversation do
  use GenServer
  alias ChatBot.{LLM, Message}

  # --- 클라이언트 API ---

  def handle_user_message(conversation_id, text) do
    pid = ensure_started(conversation_id)
    GenServer.cast(pid, {:user_message, text})
  end

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

  def start_link(conversation_id) do
    GenServer.start_link(__MODULE__, conversation_id, name: via(conversation_id))
  end

  defp via(id), do: {:via, Registry, {ChatBot.ConversationRegistry, id}}

  # --- 서버 콜백 ---

  @impl true
  def init(conversation_id) do
    history = Message.recent(conversation_id)   # DB 에서 최근 대화 로드
    {:ok, %{id: conversation_id, history: history}}
  end

  @impl true
  def handle_cast({:user_message, text}, state) do
    # 요청마다 감독되는 Task 로 격리 → 한 요청의 지연/실패가 다른 요청을 막지 않음
    Task.Supervisor.start_child(ChatBot.TaskSupervisor, fn ->
      LLM.stream_reply(state.id, state.history, text)
    end)
    {:noreply, %{state | history: state.history ++ [%{role: "user", content: text}]}}
  end
end
```

여기서 몇 가지를 짚어보자.

**`{:via, Registry, ...}` 이름 등록.** `start_link` 는 GenServer 를 시작하면서 `name: via(conversation_id)` 를 넘긴다. `via/1` 이 돌려주는 `{:via, Registry, {ChatBot.ConversationRegistry, id}}` 튜플은 "이 프로세스의 이름을 Registry 에 이 키로 등록하라"는 지시다. 등록은 프로세스가 뜨는 순간 자동으로 이뤄지고, 프로세스가 죽으면 Registry 항목도 자동으로 사라진다. 죽은 pid 가 매핑에 남아 있을 걱정을 할 필요가 없다는 뜻이다. Go 나 Java 라면 `map[conversationId]*Conversation` 같은 자료구조를 직접 두고, 잠금(lock)으로 보호하고, 프로세스가 죽었을 때 항목을 지우는 정리 로직까지 손으로 짜야 한다. Registry 는 그 전부를 런타임이 대신 해준다.

**`ensure_started` 의 조회-없으면-생성 패턴.** `Registry.lookup/2` 로 pid 를 찾고, 없으면(`[]`) `DynamicSupervisor.start_child/2` 로 새 대화 프로세스를 감독 트리 아래에 붙인다. `DynamicSupervisor` 는 실행 중에 자식을 동적으로 추가·제거할 수 있는 감독자다. 여기서 태어난 모든 대화 프로세스는 이 감독자의 자식이 되므로, 하나가 크래시해도 감독자의 정책에 따라 처리되고 나머지 형제 프로세스에는 영향이 없다.

**init 에서 히스토리 로드.** 프로세스가 처음 뜰 때 `init/1` 은 `Message.recent(conversation_id)` 로 DB(`messages` 테이블)에서 최근 대화 기록을 읽어 상태(`history`)에 담는다. 7편에서 정의한 스키마의 `messages(id, conversation_id, role, content, inserted_at)` 가 그 저장소다. 이렇게 한 번 로드해 두면, 이후로는 매 메시지마다 DB 를 다시 뒤질 필요 없이 메모리 안의 살아 있는 컨텍스트로 대화를 이어갈 수 있다.

## 왜 상태를 프로세스에 두는가

전형적인 무상태 웹 백엔드였다면 대화 히스토리를 매 요청마다 Redis 같은 외부 저장소에서 읽어 오고, 처리한 뒤 다시 직렬화해서 써 넣었을 것이다. 요청이 들어올 때마다 역직렬화, 나갈 때마다 직렬화 — 대화가 길어질수록 이 왕복 비용은 커진다.

프로세스에 상태를 두면 이 왕복이 사라진다. `history` 는 GenServer 프로세스의 메모리 안에 **살아 있는 컨텍스트**로 존재한다. 사용자의 다음 메시지가 도착하면 이미 로드된 히스토리에 곧바로 얹으면 된다. 직렬화도, 캐시 무효화도, "이 캐시가 최신인가"를 걱정할 일도 없다. 상태의 소유자가 명확히 하나(그 대화의 프로세스)이기 때문이다.

두 번째 이점은 **격리성**이다. 각 대화가 독립된 프로세스이므로, 한 대화에서 예외가 터지거나 LLM 호출이 이상한 응답으로 프로세스를 죽여도 그 여파는 **딱 그 대화 하나**에 갇힌다. 다른 수천 개의 대화는 자기 프로세스 안에서 아무 일도 없었다는 듯 계속 돌아간다. 1막에서 "한 프로세스가 죽어도 공유 힙이 없어 다른 프로세스는 멀쩡하다"고 말한 그 격리성이, 여기서는 "한 사용자의 대화가 꼬여도 다른 사용자는 영향받지 않는다"는 실전 속성으로 재현된다. 공유 메모리를 쓰는 런타임에서는 이 격리를 얻기 위해 프로세스 경계를 인위적으로 세우거나, 하나의 스레드 풀을 공유하며 서로의 실패에 노출되는 위험을 감수해야 한다.

## 요청당 Task 격리

대화 프로세스에 상태를 둔 것까지는 좋다. 하지만 여기에 함정이 하나 있다. GenServer 는 메시지를 **한 번에 하나씩** 순차적으로 처리한다. `handle_user_message/2` 가 쓰는 `GenServer.cast` 는 답을 기다리지 않고 상대 프로세스의 mailbox 에 메시지를 넣고 바로 돌아오는 비동기 전송이고, 그 메시지를 서버 쪽에서 받는 콜백이 `handle_cast` 다. 만약 `handle_cast({:user_message, ...})` 안에서 LLM API 를 직접 호출해 버리면, 그 호출이 끝날 때까지 — 수 초가 걸릴 수도 있는 그 시간 동안 — 이 대화 프로세스의 메일박스는 꽉 막힌다. 스트리밍 응답을 받는 내내 이 대화는 다른 어떤 메시지도 처리하지 못하는 것이다.

해법은 느린 작업을 프로세스 밖으로 밀어내는 것이다. `handle_cast` 는 LLM 호출을 직접 하지 않고, `Task.Supervisor.start_child(ChatBot.TaskSupervisor, ...)` 로 **감독되는 Task** 를 하나 띄워 그 안에서 `LLM.stream_reply/3` 를 실행하게 한다. 그러고는 즉시 `{:noreply, ...}` 로 반환한다. 대화 프로세스는 히스토리에 사용자 메시지만 얹고 곧바로 다음 메시지를 받을 수 있는 상태로 돌아간다. 실제 LLM 호출과 토큰 스트리밍은 별도의 Task 프로세스가 담당한다.

이 분리가 주는 것은 세 가지다. 첫째, **메일박스가 막히지 않는다.** 느리거나 실패하는 LLM 호출이 대화 프로세스의 처리 흐름을 붙잡지 않는다. 둘째, **동시 fan-out 이 자연스럽다.** (fan-out = 입력 하나를 여러 독립 작업·수신자로 펼치는 것.) 여러 대화가 동시에 메시지를 받으면 각자의 Task 가 병렬로 뜨고, 수백·수천 개의 LLM 호출이 동시에 진행된다. 이것이 2편에서 말한 경량 동시성이 실제 워크로드에서 값을 하는 지점이다. 셋째, **Task 도 감독된다.** `ChatBot.TaskSupervisor`(`Task.Supervisor`) 아래에서 돌기 때문에, Task 가 크래시해도 그 사실이 감독자에게 보고되고 대화 프로세스 자체는 무사하다.

다만 "감독된다"는 말을 오해하지 말자. 여기서 supervised 는 **caller 와 분리된 별도의 child 로 관리된다**는 뜻이지, **자동 retry** 를 뜻하지 않는다. `Task.Supervisor.start_child/2` 의 기본 restart 는 `:temporary` 라 Task 가 크래시해도 재시작되지 않는다. 게다가 위처럼 fire-and-forget 으로 띄우면 Task 의 결과도, 실패도 대화 프로세스로 전달되지 않는다. 제대로 하려면 Task 결과를 Conversation 으로 돌려보내 `{:ok, full_text} | {:error, reason}` 을 처리하고, 정말 재시도가 필요한 작업이라면 in-process Task 대신 durable 한 Oban 잡으로 옮겨야 한다. 이 글의 코드는 격리와 스트리밍 흐름을 보여주는 데 초점을 맞춘, 그 앞 단계의 축약본이다.

## LLM 스트리밍 클라이언트

이제 Task 안에서 실제로 도는 코드, `ChatBot.LLM` 을 보자. Anthropic Messages API 를 `Req` 로 호출하고, SSE(Server-Sent Events) 스트림으로 돌아오는 토큰 조각을 받아 사용자에게 흘려보낸다.

```elixir
defmodule ChatBot.LLM do
  @moduledoc "Anthropic Messages API 호출 + 토큰 스트리밍"
  alias ChatBot.{Repo, Message, Channels}

  @endpoint "https://api.anthropic.com/v1/messages"

  def stream_reply(conversation_id, history, user_text) do
    body = %{
      model: "claude-opus-4-8",
      max_tokens: 1024,
      stream: true,
      system: "너는 친절한 어시스턴트다.",
      messages: build_messages(history, user_text)
    }

    # Req 의 :into 콜백으로 SSE 청크를 받아 토큰을 누적/스트리밍한다.
    Req.post!(@endpoint,
      headers: [
        {"x-api-key", System.fetch_env!("ANTHROPIC_API_KEY")},
        {"anthropic-version", "2023-06-01"}
      ],
      json: body,
      into: fn {:data, chunk}, {req, resp} ->
        for token <- parse_sse_tokens(chunk) do
          # 예: 사용자 채널로 부분 응답 전송 (Phoenix.PubSub 브로드캐스트도 가능)
          handle_token(conversation_id, token)
        end
        {:cont, {req, resp}}
      end
    )
  end

  defp build_messages(history, user_text) do
    Enum.map(history, &%{role: &1.role, content: &1.content}) ++
      [%{role: "user", content: user_text}]
  end

  # SSE 청크에서 content_block_delta 이면서 delta.type 이 text_delta 인 것의 text 만 뽑아낸다.
  defp parse_sse_tokens(chunk) do
    chunk
    |> String.split("\n")
    |> Enum.filter(&String.starts_with?(&1, "data: "))
    |> Enum.map(&String.replace_prefix(&1, "data: ", ""))
    |> Enum.flat_map(fn json ->
      case Jason.decode(json) do
        {:ok, %{"type" => "content_block_delta", "delta" => %{"type" => "text_delta", "text" => text}}} ->
          [text]
        _ ->
          []
      end
    end)
  end

  defp handle_token(_conversation_id, _token), do: :ok  # 아래에서 구체화
end
```

이 코드에서 정확히 지켜야 하는 사실들이 있다. Java 나 Go 의 SDK 감각으로 임의로 필드를 추가하면 요청이 400 으로 튕긴다.

- **엔드포인트:** `POST https://api.anthropic.com/v1/messages`.
- **헤더:** 인증은 `Authorization: Bearer` 가 아니라 `x-api-key` 다. 그리고 `anthropic-version: 2023-06-01` 을 반드시 함께 보낸다.
- **본문:** `model` 은 `"claude-opus-4-8"`, `max_tokens` 필수, `stream: true` 로 스트리밍을 켠다. `system`(시스템 프롬프트)과 `messages`(대화 배열)를 넘긴다.
- **temperature / top_p / top_k 는 넣지 않는다.** Opus 4.8 에서는 이 세 가지 샘플링 파라미터 중 **어느 것이든 비기본값으로 설정하면 400** 이다. 그래서 이 예제는 세 필드를 모두 생략한다. 습관적으로 `temperature: 0.7` 을 붙이지 말 것.
- **SSE 파싱:** 스트림은 `data: {...}` 형태의 줄로 온다. 그중 `type` 이 `content_block_delta` 인 이벤트의 `delta.text` 가 실제 토큰 조각이다. `message_stop` 이벤트가 스트림의 끝을 알린다.

핵심은 `Req.post!` 의 `:into` 옵션이다. 응답 전체를 메모리에 다 받은 뒤 처리하는 게 아니라, 바이트 청크가 도착할 때마다 콜백이 호출된다. 콜백은 `parse_sse_tokens/1` 로 그 청크에서 토큰들을 뽑아 `handle_token/2` 로 넘긴다. `handle_token` 은 규약에서 자리만 잡아 둔 함수인데, 실전에서는 이렇게 채운다.

```elixir
defp handle_token(conversation_id, token) do
  # 부분 응답을 그 대화를 구독 중인 곳(웹소켓/채널)으로 브로드캐스트
  Phoenix.PubSub.broadcast(
    ChatBot.PubSub,
    "conversation:#{conversation_id}",
    {:token, token}
  )
end
```

`Phoenix.PubSub.broadcast/3` 로 `"conversation:#{id}"` 토픽에 토큰을 뿌리면, 그 토픽을 구독 중인 채널 프로세스(예: 사용자의 웹소켓을 쥔 프로세스)가 토큰을 받아 즉시 사용자에게 전달한다. 채널 어댑터로 직접 `Channels.send_message/2` 를 호출해 부분 텍스트를 흘려보내도 되지만, PubSub 를 한 겹 두면 "누가 이 대화를 듣고 있는가"와 "누가 응답을 생성하는가"를 깔끔하게 분리할 수 있다. 한 대화를 여러 클라이언트가 동시에 지켜보는 경우(예: 웹과 모바일 동시 접속)에도 브로드캐스트 한 번으로 모두에게 닿는다.

### SSE 파싱 주의

한 가지 정직하게 경고해 둔다. 위 `parse_sse_tokens/1` 는 **교육용 단순화**다. 흐름을 명확히 보여주려고 세 가지 현실을 생략했으니, 프로덕션에서는 반드시 채워야 한다.

첫째, **줄/프레임 버퍼링**이 필요하다. 실제 네트워크에서는 하나의 SSE 프레임(이벤트끼리는 빈 줄로 구분된다)이 여러 TCP 청크에 걸쳐 잘려 도착할 수 있다 — 즉 `data: {...}` 한 줄이 청크 경계에서 반토막 날 수 있다. 청크 단위로 즉석에서 `String.split("\n")` 하면 이런 반토막 줄은 JSON 디코딩에 실패해 조용히 버려진다. 아직 완결되지 않은 마지막 줄을 다음 청크까지 들고 가는 라인 버퍼링(직전 청크의 나머지를 상태로 유지하다가, 개행을 만나면 그제서야 완결된 줄로 파싱)이 있어야 한다.

둘째, **에러를 실패로 처리**해야 한다. 스트림 도중 `type: "error"` 이벤트가 올 수 있고, 애초에 응답이 non-2xx 로 떨어질 수도 있다. 위 코드는 이런 경우를 조용히 무시하지만, 실제로는 이를 실패로 감지해 Task 를 에러로 종료시키고 상위에서 처리해야 한다.

셋째, **스트림 종료는 `message_stop` 로 판단**한다. OpenAI 관용구인 `data: [DONE]` sentinel 은 Anthropic `anthropic-version: 2023-06-01` 스트림에는 오지 않는다. 끝을 알리는 것은 `message_stop` 이벤트다.

## 응답 저장

스트리밍이 끝나면 두 가지를 마무리해야 한다. 완성된 어시스턴트 응답을 `messages` 테이블에 **영속화**하고, 대화 프로세스의 히스토리도 **갱신**해야 한다. 그래야 프로세스가 나중에 재시작되더라도 `init/1` 이 이 응답까지 포함한 히스토리를 다시 로드할 수 있다.

먼저 분명히 해 두자. 앞서 본 `ChatBot.LLM` 코드는 **SSE 파싱과 토큰 스트리밍만 보여주는 축약본**이다. 실제 구현은 세 가지를 더 해야 한다 — (a) Task 를 시작하기 **전에** user 메시지를 DB(`messages` 테이블)에 저장하고, (b) `:into` 콜백의 스트림 accumulator 에 토큰을 이어 붙여 `full_text` 를 누적한 뒤, (c) 정상 `message_stop` 에서 assistant 메시지를 저장하고 대화 프로세스의 히스토리를 갱신한다. (a) 와 (c) 를 모두 DB 에 남겨야 재시작 시 `init/1` 이 대화를 온전히 복원할 수 있다. 아래는 그중 (c) 의 저장·갱신 부분만 떼어 본 것으로, 평범한 Ecto insert 다.

```elixir
defp save_assistant_reply(conversation_id, full_text) do
  # 1) messages 테이블에 assistant 응답 영속화
  %Message{}
  |> Message.changeset(%{
    conversation_id: conversation_id,
    role: "assistant",
    content: full_text
  })
  |> Repo.insert()

  # 2) 대화 프로세스의 히스토리 갱신 (다음 턴의 컨텍스트)
  GenServer.cast(
    {:via, Registry, {ChatBot.ConversationRegistry, conversation_id}},
    {:assistant_message, full_text}
  )
end
```

Task 는 GenServer 상태를 직접 만질 수 없으므로(상태의 소유자는 어디까지나 대화 프로세스다), `{:assistant_message, full_text}` 를 `cast` 로 되돌려 보낸다. Registry 에 등록된 `via` 이름으로 캐스트하면 정확히 그 대화 프로세스에 닿는다. 대화 프로세스는 이 메시지를 받아 히스토리에 어시스턴트 응답을 얹는다.

```elixir
@impl true
def handle_cast({:assistant_message, text}, state) do
  {:noreply, %{state | history: state.history ++ [%{role: "assistant", content: text}]}}
end
```

이렇게 하면 상태 변경이 전부 대화 프로세스 한 곳으로 직렬화되어 들어온다. 사용자 메시지 추가도, 어시스턴트 응답 추가도 모두 그 프로세스의 메일박스를 거치므로, `history` map 을 **동시에 쓰다가 깨지는** 종류의 경쟁 조건은 없다. 잠금 없이도 map 쓰기가 안전한 이유가 바로 이것이다.

**하지만 한 가지 오해는 짚고 넘어가야 한다.** "요청마다 감독되는 Task 라 경쟁 조건이 원천적으로 없다"는 말은 **틀렸다.** GenServer 가 map 쓰기를 직렬화하는 것과, **대화 turn 의 순서를 보장하는 것은 전혀 다른 문제**다. 같은 대화에 user 메시지가 연달아 들어오는 상황을 생각해 보자. 첫 메시지의 Task 가 아직 스트리밍 중인데 두 번째 메시지가 도착하면, `handle_cast` 는 곧바로 두 번째 Task 를 띄운다. 두 Task 는 각자 **서로 다른(오래된) history snapshot** 으로 동시에 LLM 을 호출하고, 응답 저장이 도착하는 순서도 뒤섞일 수 있다 — 최악의 경우 히스토리가 `user1, user2, assistant2, assistant1` 처럼 꼬인다.

그래서 규칙은 이렇게 잡아야 한다. **서로 다른 대화의 LLM 호출은 동시에 실행해도 되지만, 같은 대화의 turn 은 한 번에 하나만** 실행한다. 진행 중인 Task 가 있으면 다음 user 메시지를 큐에 넣어 두고, assistant 응답 저장이 끝난 뒤에야 다음 Task 를 시작한다. 개념적으로는 Conversation state 에 `busy?` 플래그와 대기 큐를 두는 식이다.

```elixir
# 개념 수준 스케치 — 같은 대화의 turn 을 직렬화한다
def handle_cast({:user_message, text}, %{busy?: true} = state) do
  # 이미 진행 중인 turn 이 있으면 큐에 쌓아 둔다
  {:noreply, %{state | queue: state.queue ++ [text]}}
end

def handle_cast({:user_message, text}, %{busy?: false} = state) do
  start_reply_task(state.id, state.history, text)
  {:noreply, %{state | busy?: true,
                       history: state.history ++ [%{role: "user", content: text}]}}
end

# assistant 응답 저장이 끝나 turn 이 닫힐 때 호출된다 → 큐에 있으면 다음 turn 시작
def handle_cast({:turn_done, assistant_text}, state) do
  state = %{state | history: state.history ++ [%{role: "assistant", content: assistant_text}]}

  case state.queue do
    [] -> {:noreply, %{state | busy?: false}}
    [next | rest] ->
      start_reply_task(state.id, state.history, next)
      {:noreply, %{state | queue: rest,
                           history: state.history ++ [%{role: "user", content: next}]}}
  end
end
```

이 글의 앞선 `handle_cast` 코드는 흐름을 단순하게 보여주려고 이 큐잉을 생략했지만, 같은 대화가 빠르게 연달아 메시지를 받는 실제 서비스라면 반드시 필요한 부분이다.

## 전체 흐름 정리

지금까지 만든 조각들을 하나의 경로로 이어 보자.

1. **사용자 메시지** 가 어떤 채널(Telegram/Slack/…)로 도착한다.
2. 채널 어댑터가 이를 `ChatBot.InboundMessage` 로 정규화하고 **Router** 에 넘긴다.
3. Router 는 신원 매핑으로 대화를 찾아 `Conversation.handle_user_message/2` 를 호출한다.
4. **Conversation GenServer** 가 Registry 조회로 자기 pid 를 확인(없으면 DynamicSupervisor 로 시작)하고, `handle_cast` 에서 히스토리에 사용자 메시지를 얹는다.
5. 같은 `handle_cast` 가 **Task.Supervisor** 로 감독되는 Task 를 띄운다.
6. Task 안에서 **`LLM.stream_reply/3`** 가 Anthropic Messages API 를 `stream: true` 로 호출하고, **SSE** 청크를 `:into` 콜백으로 받는다.
7. 청크에서 뽑은 **토큰을 스트리밍** — `handle_token` 이 PubSub 로 브로드캐스트한다.
8. 구독 중인 채널 프로세스가 토큰을 받아 **사용자에게 전송** 한다.
9. 스트림이 끝나면 완성된 응답을 `messages` 에 **저장** 하고, `cast` 로 대화 프로세스의 히스토리를 갱신한다.

## 개념이 코드가 되는 지점

이 구조를 한 걸음 물러나서 보면, 1막과 2막에서 이야기한 세 축이 LLM 워크로드 위에서 그대로 구현되어 있다.

- **동시성** — 수많은 동시 대화가 각자의 GenServer 로, 각 LLM 호출이 각자의 Task 로 존재한다. 수천 개의 대화와 수천 개의 진행 중인 스트리밍이 경량 프로세스로 자연스럽게 공존한다.
- **격리성** — 대화별 프로세스 경계 덕분에, 한 대화의 실패(꼬인 상태, 죽어버린 LLM Task)가 다른 대화로 번지지 않는다. 상태는 공유되지 않고 각 프로세스 안에 갇혀 있다.
- **감독성** — 대화 프로세스는 `DynamicSupervisor` 아래, LLM Task 는 `Task.Supervisor` 아래에서 감독된다. 크래시는 보고되고 격리되며, 죽은 조각이 살아 있는 조각을 끌어내리지 않는다.

Redis 로 상태를 직렬화하고, 잠금으로 맵을 보호하고, 재시작 로직을 손으로 짜는 대신 — Registry, DynamicSupervisor, Task.Supervisor 라는 런타임 기본기가 이 전부를 대신했다. POC 의 심장은 이렇게 뛴다.

다음 글에서는 이 심장이 과부하 상황에서도 멈추지 않도록 하는 법 — 부하 조절과 내구성 — 을 다룬다. LLM 프로바이더의 rate limit 을 지키고, 장애를 서킷브레이커로 차단하고, 크래시에도 인바운드 메시지를 잃지 않게 만드는 이야기다.

다음 글: [부하 조절과 내구성, 그리고 POC 너머](09-throttling-durability.md)
