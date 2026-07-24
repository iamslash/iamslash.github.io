# 채널 게이트웨이: 어댑터 패턴

이 글은 "대용량 메시지 처리 도구: Erlang 에서 Elixir 까지" 9부작 시리즈의 일곱 번째 글이다. 앞선 6편에서는 멀티채널 LLM 챗봇 게이트웨이의 전체 그림 — Elixir + PostgreSQL 만으로 대화당 프로세스를 띄우고, 채널은 어댑터로 갈아 끼우고, Kafka/Scylla 는 아직 필요 없다는 판단 — 을 시스템 설계 관점에서 조망했다. 이번 글에서는 그 그림의 맨 앞단, 사용자의 메시지가 시스템 안으로 들어오는 관문인 **채널 게이트웨이**를 코드로 구현한다. 핵심 도구는 하나, 어댑터 패턴이다. iMessage 를 LinQ 라는 게이트웨이 뒤에 숨기고, 나중에 Slack/Discord 를 어댑터 모듈 하나씩 추가하는 것만으로 확장하는 구조를 만들 것이다.

## 문제: 채널마다 다르고, 코어는 그걸 몰라야 한다

챗봇이 상대해야 하는 채널은 저마다 방언이 다르다. Telegram 은 봇 API 로 웹훅을 쏘고 `sendMessage` 로 답을 받는다. Slack 은 Events API 와 서명 검증, 그리고 별도의 Web API 를 쓴다. Discord 는 게이트웨이 웹소켓과 REST 를 섞는다. iMessage 는 — 뒤에서 정직하게 다루겠지만 — 공식 봇 API 자체가 없다. 프로토콜도, 인증 방식도, 메시지 JSON 의 필드 이름도 전부 제각각이다.

여기서 유혹은 늘 같다. "일단 Telegram 부터 붙이자"며 봇의 대화 로직 안에 Telegram 의 `chat.id` 와 `message.text` 를 직접 박아 넣는 것이다. 그러면 두 번째 채널을 붙이는 순간 대화 코어를 다시 뜯어야 한다. 우리가 원하는 건 정반대다. **대화 코어(라우터, 대화 프로세스, LLM 호출)는 메시지가 어느 채널에서 왔는지 몰라야 한다.** 채널의 특수성은 전부 얇은 어댑터 계층에 가두고, 그 계층이 바깥의 온갖 방언을 하나의 표준 형태로 번역해서 코어에 넘긴다. 이것이 어댑터 패턴이고, Elixir 에서는 이를 **behaviour** 로 아주 자연스럽게 표현한다.

> **Java/Go 독자를 위한 다리**: Elixir 의 behaviour 는 Java/Go 의 interface 와 비슷한 '함수 목록 계약'이다. 공통 구현을 물려주진 않지만, 그 계약을 따르겠다고 선언한 adapter 가 필요한 callback 을 빠뜨렸는지 compiler 가 확인해 준다.

## 채널 어댑터 behaviour

먼저 모든 어댑터가 코어로 넘길 "표준 형태"를 정의한다. 채널이 무엇이든 코어가 알아야 하는 것은 결국 네 가지뿐이다. 어느 채널인지, 그 채널에서의 발신자 ID 가 무엇인지, 텍스트가 무엇인지, 그리고 어떤 스레드(대화 맥락)에 속하는지.

```elixir
defmodule ChatBot.InboundMessage do
  @moduledoc "모든 채널 어댑터가 코어로 넘기는 정규화된 인바운드 메시지"
  @enforce_keys [:channel, :channel_user_id, :text]
  defstruct [:channel, :channel_user_id, :text, :thread_key]
end

defmodule ChatBot.Channel do
  @moduledoc "채널 어댑터 behaviour. Telegram/LinQ/Slack/Discord 가 각각 구현한다."

  @doc "해당 채널로 응답 텍스트를 전송한다."
  @callback send_message(channel_user_id :: String.t(), text :: String.t()) ::
              :ok | {:error, term()}
end
```

`ChatBot.Channel` behaviour 는 아웃바운드 한 방향만 계약으로 못 박는다. `send_message/2` 는 "정규화된 사용자 ID 와 텍스트를 받아 그 채널 API 로 실제 전송하라"는 규약이다. 컴파일러는 `@behaviour ChatBot.Channel` 을 선언한 모듈이 이 콜백을 구현하지 않으면 경고를 띄운다.

여기서 그 안전망의 크기를 정직하게 재두자. behaviour 가 잡아 주는 것은 **콜백의 이름·arity(인자 개수) 누락을 compiler warning 으로** 알리는 데까지다. 인자의 타입이나 값이 맞는지는 runtime 에 검사하지 않는다. 게다가 warning 은 기본적으로 build 를 막지 않는다 — CI 에서 `mix compile --warnings-as-errors` 를 걸어 두어야 그제서야 "콜백 누락 → build 실패"가 되어 배포 전에 잡힌다. 즉 "자동으로 잡힌다"가 아니라 "이 설정을 해 두면 잡힌다"가 정확한 표현이다.

한 가지 더, `send_message/2` 의 첫 인자가 `channel_user_id`(= 발신자 ID)라는 점을 눈여겨보자. 이 POC 는 1:1 대화를 가정하므로 응답 목적지가 곧 발신자라 이렇게 두었다. 하지만 일반적으로 **응답을 보낼 목적지는 발신자와 다를 수 있다**(그룹 대화가 대표적). 실무에서는 InboundMessage 에 `reply_to` 를 따로 두고 `send_message(reply_to, text)` 로 목적지를 분리한다. 이 얘기는 아래 Telegram 어댑터에서 구체적으로 다룬다.

인바운드 방향은 어디 있냐고 물을 수 있다. 인바운드 정규화 — 채널의 원본 페이로드를 `InboundMessage` 로 바꾸는 일 — 는 채널마다 입력 모양이 너무 달라서(Telegram 은 웹훅 JSON, Slack 은 서명된 이벤트, 웹소켓 채널은 프레임) 하나의 콜백 시그니처로 묶기 어렵다. 그래서 우리는 이 방향을 behaviour 로 강제하는 대신 각 어댑터의 `normalize/1` 관례 함수로 둔다. 규약은 단순하다. **각 어댑터는 (1) 자기 채널의 인바운드를 `InboundMessage` 로 정규화하고, (2) `send_message/2` 로 아웃바운드를 자기 채널 API 로 전송한다.** behaviour 가 (2)를 컴파일 타임에 보장하고, (1)은 어댑터 안에서 패턴 매칭으로 처리한다.

## 라우터: 어댑터에서 코어로 들어가는 단 하나의 문

정규화가 끝난 `InboundMessage` 는 이제 채널색이 완전히 빠진 상태다. 이 표준 메시지가 코어로 들어가는 입구가 라우터다.

```elixir
defmodule ChatBot.Router do
  alias ChatBot.{InboundMessage, Identity, Conversation}

  @doc "정규화된 인바운드 메시지를 받아 해당 대화 프로세스로 라우팅한다."
  def route(%InboundMessage{} = msg) do
    conversation = Identity.resolve_conversation(msg)   # 신원 매핑 → 대화 찾기/생성
    Conversation.handle_user_message(conversation.id, msg.text)
  end
end
```

`route/1` 의 함수 헤드가 `%InboundMessage{}` 패턴을 강제한다는 점을 눈여겨보자. 원본 Telegram 맵이나 LinQ 페이로드가 실수로 여기까지 새어 들어오면 함수 절 매칭에서 곧바로 터진다. 코어는 오직 정규화된 구조체만 받는다는 것이 타입이 아니라 코드로 보장된다. 라우터가 하는 일은 딱 두 가지다. 먼저 이 메시지가 어느 대화에 속하는지 신원 매핑으로 해석하고(`Identity.resolve_conversation/1`), 그 대화 프로세스에 사용자 메시지를 던진다(`Conversation.handle_user_message/2`). 대화 프로세스 쪽 — GenServer 상태와 LLM 스트리밍 — 은 다음 8편의 주제이므로, 여기서는 앞의 절반, 즉 신원 매핑에 집중한다.

## 신원 매핑: 멀티채널이면 반드시 필요하다

이 부분이 멀티채널 게이트웨이의 숨은 심장이다. 단일 채널만 쓴다면 "Telegram chat_id = 사용자"로 끝나서 신원 매핑이 필요 없다. 하지만 채널이 둘 이상 되는 순간 문제가 생긴다. 같은 사람이 회사에서는 Slack 으로, 집에서는 iMessage 로 같은 봇에게 말을 건다. Telegram 의 `789`, iMessage 의 `+821012345678`, Slack 의 `U0ABC` 는 서로 완전히 다른 문자열이지만 **한 사람**이다. 채널 ID 를 그대로 사용자 키로 쓰면, 이 한 사람이 시스템 안에서 세 명의 유령으로 쪼개진다. 대화 이력도, 개인화 컨텍스트도 채널 경계에서 끊긴다.

해결책은 채널 ID 와 우리 시스템의 정규 사용자(canonical user)를 분리하고, 그 사이를 잇는 매핑 테이블을 두는 것이다. 6편에서 예고한 스키마가 바로 이 구조다.

```
users(id, inserted_at)
user_identities(id, user_id → users.id, channel, channel_user_id)   -- 채널별 신원 매핑
conversations(id, user_id → users.id, channel, thread_key, inserted_at)
messages(id, conversation_id → conversations.id, role, content, inserted_at)  -- role: "user" | "assistant"
```

`user_identities` 가 핵심이다. 한 명의 `users` 레코드에 여러 개의 `(channel, channel_user_id)` 행이 매달린다. `(telegram, "789")`, `(imessage, "+82...")`, `(slack, "U0ABC")` 세 행이 모두 같은 `user_id` 를 가리키면, 세 채널의 그 사람이 한 명으로 묶인다. Ecto 스키마로 옮기면 이렇다.

```elixir
defmodule ChatBot.Accounts.User do
  use Ecto.Schema

  schema "users" do
    has_many :identities, ChatBot.Accounts.UserIdentity
    timestamps(updated_at: false)
  end
end

defmodule ChatBot.Accounts.UserIdentity do
  use Ecto.Schema

  schema "user_identities" do
    field :channel, :string          # "telegram" | "imessage" | "slack" | "discord"
    field :channel_user_id, :string  # 그 채널에서의 발신자 ID
    belongs_to :user, ChatBot.Accounts.User
  end
end

defmodule ChatBot.Conversations.Conversation do
  use Ecto.Schema

  schema "conversations" do
    field :channel, :string
    field :thread_key, :string       # 채널 안에서 대화 맥락을 구분하는 키
    belongs_to :user, ChatBot.Accounts.User
    timestamps(updated_at: false)
  end
end
```

이제 라우터가 부르던 `Identity.resolve_conversation/1` 을 구현한다. 이 함수가 `(channel, channel_user_id)` 를 받아 사용자를 찾거나 만들고, 그 사용자의 대화를 찾거나 만들어서 돌려준다. `user_identities` 에 `(channel, channel_user_id)` 유니크 제약을, `conversations` 에 `(user_id, channel, thread_key)` 유니크 제약을 걸어 두었다고 가정한다.

여기서 한 가지 정확히 짚을 게 있다. 대화(conversation) 쪽은 `Repo.insert` 의 `on_conflict` 옵션으로 "있으면 가져오고 없으면 만드는" **원자적 upsert** 를 한 방에 표현할 수 있다. 하지만 사용자(user) 쪽은 다르다. "먼저 `Repo.one` 으로 찾아보고 없으면 `insert`" 하는 방식(check-then-insert)은 **원자적 upsert 가 아니다.** 같은 채널 ID 로 동시에 처음 들어온 두 요청이 둘 다 "없음"을 보고 각각 새 User 를 만들려 하면, `(channel, channel_user_id)` 유니크 제약 때문에 한쪽의 identity insert 가 충돌한다. 그래서 이 충돌을 **에러가 아니라 정상 분기로** 처리해야 한다 — 충돌한 쪽은 자기가 만들던 것을 롤백하고, 먼저 성공한 쪽이 넣은 identity 로 사용자를 재조회한다. (transaction 안에서 대상 row 를 잠그고 재조회하는 방법도 있다.) 아래 코드가 그 처리를 담고, `{:error, reason}` 경로도 명시적으로 다룬다.

```elixir
defmodule ChatBot.Identity do
  import Ecto.Query
  alias ChatBot.Repo
  alias ChatBot.Accounts.{User, UserIdentity}
  alias ChatBot.Conversations.Conversation
  alias ChatBot.InboundMessage

  @doc "정규화 메시지 → (channel, channel_user_id) → user → conversation 을 찾거나 생성한다."
  def resolve_conversation(%InboundMessage{} = msg) do
    user = resolve_user(msg.channel, msg.channel_user_id)
    thread_key = msg.thread_key || msg.channel_user_id
    find_or_create_conversation(user, msg.channel, thread_key)
  end

  defp resolve_user(channel, channel_user_id) do
    case fetch_user(channel, channel_user_id) do
      %User{} = user -> user
      nil -> create_user_with_identity(channel, channel_user_id)
    end
  end

  defp fetch_user(channel, channel_user_id) do
    query =
      from u in User,
        join: i in UserIdentity,
        on: i.user_id == u.id,
        where: i.channel == ^channel and i.channel_user_id == ^channel_user_id

    Repo.one(query)
  end

  defp create_user_with_identity(channel, channel_user_id) do
    # 주의: check-then-insert 는 원자적 upsert 가 아니다.
    # 같은 (channel, channel_user_id) 로 동시에 처음 들어온 두 요청이 각각 User 를
    # 만들려 하면, (channel, channel_user_id) unique 제약 때문에 identity insert 는
    # 한쪽만 성공한다. 진 쪽은 트랜잭션을 통째로 롤백(방금 만든 User 도 취소)하고,
    # 이긴 쪽이 넣은 identity 로 사용자를 재조회한다.
    #
    # 신규 채널로 처음 말을 건 사람은 여기서 새 canonical user 가 된다.
    # (기존 사용자와의 병합은 별도의 링크 플로우로 처리한다 — 아래 참고)
    result =
      Repo.transaction(fn ->
        user = Repo.insert!(%User{})

        {:ok, identity} =
          Repo.insert(
            %UserIdentity{user_id: user.id, channel: channel, channel_user_id: channel_user_id},
            on_conflict: :nothing,
            conflict_target: [:channel, :channel_user_id]
          )

        # on_conflict: :nothing 이 충돌을 삼키면 새 row 가 없어 identity.id 는 nil 이다.
        # → 경쟁에서 진 것이므로 롤백해 방금 만든 User 까지 되돌린다.
        if is_nil(identity.id), do: Repo.rollback(:already_exists), else: user
      end)

    case result do
      {:ok, %User{} = user} -> user
      {:error, :already_exists} -> fetch_user(channel, channel_user_id)  # 이긴 쪽 사용자 재조회
      {:error, reason} -> raise "resolve_user failed: #{inspect(reason)}"
    end
  end

  defp find_or_create_conversation(user, channel, thread_key) do
    Repo.insert!(
      %Conversation{user_id: user.id, channel: channel, thread_key: thread_key},
      on_conflict: [set: [user_id: user.id]],
      conflict_target: [:user_id, :channel, :thread_key],
      returning: true
    )
  end
end
```

한 가지 정직하게 짚어둘 점. 위 코드는 신규 채널 ID 를 만나면 **새 canonical user** 를 만든다. 같은 사람이 Slack 에 이어 iMessage 로 처음 들어오면, 시스템은 그를 일단 새 사용자로 본다. 두 신원을 한 사람으로 병합하는 것 — "이 Slack 계정과 이 iMessage 번호는 같은 사람"이라고 잇는 일 — 은 자동으로 추측하면 위험하므로, 보통 별도의 명시적 링크 플로우(예: 한쪽 채널에서 인증 코드를 받아 다른 쪽에서 입력)로 처리하고 `user_identities` 에 행을 하나 더 추가한다. 매핑 테이블을 분리해 둔 덕분에, 병합은 스키마 변경 없이 행 추가/`user_id` 재지정만으로 끝난다. 이 유연성이 바로 채널 ID 를 사용자 키로 직접 쓰지 않은 대가로 얻는 것이다.

## 구체 어댑터 (1): Telegram — 재현 가능한 스탠드인

이제 behaviour 를 실제로 구현하는 어댑터를 보자. 첫 번째는 Telegram 이다. 이 시리즈의 프로토타입 기본 채널로 Telegram 을 고른 이유는 단순하다. **공식 봇 API 가 있고 누구나 재현할 수 있기 때문이다.** BotFather 로 토큰을 하나 받으면, 인바운드는 웹훅으로 JSON 이 날아오고 아웃바운드는 `sendMessage` REST 호출이 전부다.

인바운드부터 보자. 여기서 6편에서 약속한 원칙 하나를 코드로 지켜야 한다. **처리에 앞서 먼저 영속화한다.** 컨트롤러가 곧장 `Router.route/1` 을 부르고 200 을 돌려주면, 라우팅 도중 프로세스가 죽는 순간 그 메시지는 사라진다(Telegram 은 200 을 받았으니 재전송하지 않는다). 그래서 컨트롤러는 `normalize/1` 로 `InboundMessage` 를 만든 뒤, **실제 처리 대신 Oban 잡으로 DB 에 먼저 넣고**, 그 insert 가 커밋된 뒤에야 200 을 반환한다. 실제 `Router.route/1` 은 그 잡을 집어가는 **worker** 가 수행한다.

여기서 Oban 의 성질을 정확히 알아야 한다. **Oban 은 at-least-once 다 — 정확히 한 번이 아니다.** 그래서 (1) 같은 업데이트가 두 번 들어와도 잡이 하나만 생기도록 provider 가 준 이벤트 id(Telegram 은 `update_id`)를 **idempotency key** 로 쓰고, (2) 잡이 재시도돼도 결과가 한 번만 반영되도록 worker 를 idempotent 하게 짠다.

```elixir
defmodule ChatBotWeb.TelegramController do
  use ChatBotWeb, :controller
  alias ChatBot.Channels.Telegram
  alias ChatBot.Jobs.Inbound

  def webhook(conn, params) do
    case Telegram.normalize(params) do
      {:ok, inbound} ->
        # update_id 를 idempotency key 로: 같은 업데이트가 두 번 와도 잡은 하나만.
        {:ok, _job} =
          %{update_id: params["update_id"], inbound: Map.from_struct(inbound)}
          |> Inbound.new(unique: [keys: [:update_id], period: :infinity])
          |> Oban.insert()

      :ignore ->
        :ok        # 텍스트 없는 업데이트(스티커, 상태 변화 등)는 흘려보낸다
    end

    # 잡이 DB 에 커밋된 뒤에야 200. 실제 Router.route 는 아래 worker 가 수행한다.
    send_resp(conn, 200, "ok")
  end
end
```

잡을 집어가는 worker 는 이렇게 생겼다. 컨트롤러는 "받았다"까지만 책임지고, "처리했다"는 여기서 일어난다.

```elixir
defmodule ChatBot.Jobs.Inbound do
  use Oban.Worker, queue: :inbound, max_attempts: 5
  alias ChatBot.{InboundMessage, Router}

  @impl Oban.Worker
  def perform(%Oban.Job{args: %{"inbound" => inbound}}) do
    # 잡 args 는 JSON 이라 키가 문자열이다 — InboundMessage 구조체로 되돌린다.
    msg = %InboundMessage{
      channel: inbound["channel"],
      channel_user_id: inbound["channel_user_id"],
      text: inbound["text"],
      thread_key: inbound["thread_key"]
    }

    # at-least-once 라 이 잡은 재시도로 두 번 돌 수 있다. Router.route 아래의
    # 대화 처리(대화 이력 append, LLM 호출)는 같은 메시지에 두 번 반영되지 않도록
    # idempotent 해야 한다(예: (conversation, provider event id) 로 중복 방지).
    Router.route(msg)
    :ok
  end
end
```

> **정직한 한 줄**: node 가 잡을 executing 하던 중에 죽으면 그 잡은 orphan 으로 남아 저절로 재시도되지 않는다. 이런 잡을 되살리려면 **Oban Lifeline** 플러그인을 설정해 두어야 한다. 즉 이 구조가 주는 보장은 "무조건 유실 없음"이 아니라 **durable at-least-once(재시도 가능, idempotency 로 중복 흡수)** 다.

그리고 어댑터 모듈이 인바운드 정규화와 아웃바운드 전송을 모두 담당한다.

```elixir
defmodule ChatBot.Channels.Telegram do
  @behaviour ChatBot.Channel
  alias ChatBot.InboundMessage

  @doc "Telegram 웹훅 업데이트를 InboundMessage 로 정규화한다."
  def normalize(%{"message" => %{"from" => %{"id" => from_id}, "chat" => %{"id" => chat_id}, "text" => text}}) do
    {:ok,
     %InboundMessage{
       channel: "telegram",
       channel_user_id: to_string(from_id),   # 발신자 신원 = from.id (chat.id 가 아니다)
       text: text,
       thread_key: to_string(chat_id)         # 대화 맥락/응답 목적지 = chat.id
     }}
  end

  def normalize(_other), do: :ignore

  @impl true
  def send_message(channel_user_id, text) do
    token = System.fetch_env!("TELEGRAM_BOT_TOKEN")
    url = "https://api.telegram.org/bot#{token}/sendMessage"

    # 이 POC(1:1 대화)에선 목적지 chat_id 와 발신자 channel_user_id 가 사실상 같아
    # 발신자에게 그대로 되보낸다. 일반적으로는 아래 note 처럼 목적지가 발신자와 다를 수 있다.
    case Req.post(url, json: %{chat_id: channel_user_id, text: text}) do
      {:ok, %Req.Response{status: 200}} -> :ok
      {:ok, %Req.Response{status: status}} -> {:error, {:telegram_http, status}}
      {:error, reason} -> {:error, reason}
    end
  end
end
```

> **발신자 신원과 응답 목적지는 다를 수 있다.** 위 `normalize/1` 은 `channel_user_id` 에 **`message.from.id`**(누가 보냈나)를 담고, `message.chat.id`(어디로 답하나)는 `thread_key` 로 둔다. 이 예제는 1:1(private) 대화를 가정하는데, 이때는 `from.id` 와 `chat.id` 가 사실상 일치해서 발신자에게 그대로 답해도 맞다. 하지만 **그룹 대화에선 발신자(`from.id`)와 응답 목적지(`chat.id` [+ `message_thread_id`])가 다르다.** 그래서 실무에서는 InboundMessage 에 `reply_to` 를 따로 두고 `send_message(reply_to, text)` 로 "누가 보냈나"와 "어디로 답하나"를 분리한다. 전면 리팩터링은 8편 이후로 미루되, 이 구분이 있다는 것만 기억해 두자.

`send_message/2` 위의 `@impl true` 는 이 함수가 `ChatBot.Channel` behaviour 의 콜백 구현임을 명시한다. 이 표식 덕에 콜백 **이름이나 arity(인자 개수)가 어긋나면 compiler warning** 이 뜬다(인자의 타입·값까지 runtime 에 검사해 주지는 않는다). 그리고 그 warning 이 실제로 build 를 막게 하려면 CI 에 `mix compile --warnings-as-errors` 를 걸어 두어야 한다. 아웃바운드 HTTP 는 8편의 LLM 클라이언트와 동일하게 [Req](https://hexdocs.pm/req) 라이브러리를 쓴다 — 프로토타입 전체가 HTTP 스택 하나로 통일된다.

## 구체 어댑터 (2): LinQ — iMessage 를 게이트웨이 뒤에 숨기기

두 번째 어댑터는 iMessage 다. 여기서는 정직하게 가자. **iMessage 에는 Telegram 같은 공식 봇 API 가 없다.** Apple 은 서드파티가 iMessage 로 봇을 운영하도록 열어 두지 않았다. 그래서 실무에서는 iMessage 를 다룰 수 있는 무언가 — macOS 위에서 도는 브리지, 프로바이더, 혹은 자체 인프라 — 를 두고, 그 복잡성을 감춘 내부 게이트웨이를 만든다. 이 시리즈에서는 그 게이트웨이를 **LinQ** 라고 부른다.

여기서 중요한 것은 LinQ 뒤에 무엇이 있느냐가 아니다. LinQ 는 그 지저분한 내막(브리지 관리, 세션 유지, 프로바이더 연동)을 전부 뒤에 숨기고, 바깥에는 우리에게 익숙한 형태 — **웹훅으로 인바운드를 밀어 주고, REST 로 아웃바운드를 받는다** — 로만 노출한다. 그렇게 인터페이스를 정리하고 나면, 우리 앱 입장에서 LinQ 어댑터는 Telegram 어댑터와 구조가 **똑같다**. 난이도는 코드에 있지 않고, 그 채널에 닿는 접근 경로 자체에 있다.

```elixir
defmodule ChatBot.Channels.LinQ do
  @behaviour ChatBot.Channel
  alias ChatBot.InboundMessage

  # LinQ(iMessage 게이트웨이)가 웹훅으로 밀어 주는 페이로드를 정규화한다.
  def normalize(%{"handle" => handle, "body" => body} = payload) do
    {:ok,
     %InboundMessage{
       channel: "imessage",
       channel_user_id: handle,                       # 예: "+821012345678"
       text: body,
       thread_key: payload["chat_guid"] || handle     # 그룹/개인 대화 구분
     }}
  end

  def normalize(_other), do: :ignore

  @impl true
  def send_message(channel_user_id, text) do
    base = System.fetch_env!("LINQ_BASE_URL")
    token = System.fetch_env!("LINQ_TOKEN")

    case Req.post("#{base}/messages",
           headers: [{"authorization", "Bearer #{token}"}],
           json: %{handle: channel_user_id, body: text}) do
      {:ok, %Req.Response{status: status}} when status in 200..299 -> :ok
      {:ok, %Req.Response{status: status}} -> {:error, {:linq_http, status}}
      {:error, reason} -> {:error, reason}
    end
  end
end
```

두 어댑터를 나란히 놓고 보면 요점이 선명하다. 필드 이름(`chat.id` vs `handle`, `sendMessage` vs `POST /messages`)과 인증 방식만 다를 뿐, 골격은 동일하다. `normalize/1` 로 정규화하고, `send_message/2` 로 전송한다. LinQ 컨트롤러도 위 Telegram 컨트롤러와 판박이라 지면상 생략한다 — `LinQ.normalize/1` 로 `InboundMessage` 를 만들고, 마찬가지로 Oban 잡으로 먼저 영속화(idempotency key 는 LinQ 페이로드의 이벤트 id)한 뒤 2xx 를 돌려주면 끝이다.

## 핵심 교훈: 어댑터 뒤가 무엇이든 코어는 안 바뀐다

이 구조에서 얻는 것은 한 문장으로 요약된다. **어댑터 뒤가 Telegram 이든 LinQ(iMessage)든 BlueBubbles 같은 다른 브리지든, 코어(Router / Conversation / Identity)는 단 한 줄도 바뀌지 않는다.** 채널의 방언은 전부 어댑터에 격리되고, 코어는 오직 `InboundMessage` 라는 표준어만 상대한다.

Slack 이나 Discord 를 붙이는 일도 이제 정형화된 작업이 된다. `ChatBot.Channels.Slack` 모듈을 하나 만들어 `@behaviour ChatBot.Channel` 을 선언하고, 그 채널의 이벤트를 `InboundMessage` 로 바꾸는 `normalize/1` 과, Web API 로 답을 보내는 `send_message/2` 를 구현한다. 컨트롤러(혹은 웹소켓 핸들러) 하나를 추가해 `Router.route/1` 로 이어 주면 끝이다. 라우터도, 신원 매핑도, 대화 프로세스도 손대지 않는다. 확장의 비용이 "새 어댑터 모듈 하나"로 고정된다는 것 — 이것이 어댑터 패턴이 주는 실질적 이득이다.

## 블로그 재현성에 대한 짧은 주의

이 시리즈가 예제 채널로 Telegram 을 미는 데는 교육적 이유가 있다. Telegram 은 토큰만 있으면 누구나 웹훅을 걸고 직접 돌려볼 수 있어, 독자가 코드를 그대로 재현할 수 있다. 실무에서는 같은 인터페이스 뒤에 LinQ 를 꽂는다. 둘은 서로 다른 두 시스템이 아니라, **같은 어댑터 패턴의 두 인스턴스**다. 공개 글에서는 재현 가능한 채널로 시연하고, 프로덕션에서는 그 자리에 사내 게이트웨이를 끼운다 — 코어가 채널을 모르게 설계했기에 가능한 맞바꿈이다.

## 정직한 경고: iMessage 는 수평 확장이 깔끔하지 않다

마지막으로 하나 경고해 둔다. iMessage 는 대용량 부하를 부드럽게 받아내는 채널이 아니다. 근본적으로 Apple ID 와 맥(혹은 브리지) 단위의 rate limit 에 묶여 있고, 대량 발송은 계정 정지 위험을 동반한다. LinQ 가 인터페이스를 아무리 깔끔하게 정리해도, 그 뒤의 물리적 제약 — Apple 생태계의 한계 — 까지 지워 주지는 못한다. 그래서 이 시리즈에서 대용량 부하 조절과 backpressure 를 시연할 때는 rate limit 이 명확하고 봇 API 가 열려 있는 Slack/Discord 쪽을 무대로 삼는다. iMessage 는 "붙일 수 있다"와 "무한히 밀어 넣어도 된다"가 전혀 다른 이야기라는 점을 잊지 말자. 부하와 내구성에 대한 본격적인 논의는 9편에서 다룬다.

다음 글: [대화 코어: GenServer 상태와 LLM 스트리밍](08-conversation-core.md)
