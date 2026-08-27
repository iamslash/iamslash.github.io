# 0편. 프롤로그 — Claude Code는 결국 while 루프 하나다

> 시리즈: Claude Code 내부 구조 (builtin 기준, v2.1.243)
> 이 편에서 배우는 것: LLM API에는 기억이 없다는 사실, 그런데도 대화가 이어지는 이유, 그리고 이 시리즈의 모든 주장을 직접 확인할 수 있는 관찰 도구 3종.

터미널에서 이렇게 시킵니다.

```
> 로그인 실패할 때 500 말고 401 내려주게 고쳐줘
```

그러면 Claude Code 가 알아서 파일을 찾고, 읽고, 고치고, 테스트까지 돌립니다. 처음 보면 마법 같습니다. 그런데 조금 지나면 이런 의문이 듭니다.

> **얘는 내 파일을 어떻게 읽는 거지? 그리고 아까 무슨 얘길 했는지 어떻게 기억하지?**

답부터 말하면 이렇습니다.

> **둘 다 안 합니다.** LLM 은 여러분의 파일을 읽지 못하고, 방금 한 대화도 기억하지 못합니다.

이 시리즈는 그 사이의 빈칸 — **하네스(harness)** 라고 부르는 부분 — 이 무엇을 하는지 끝까지 따라가 봅니다.

## LLM API 에는 기억이 없다

Claude API 는 놀랄 만큼 단순합니다. **메시지 배열을 받아서 다음 메시지 하나를 돌려주는 함수**입니다.

```
POST /v1/messages
{
  "model": "claude-haiku-4-5-20251001",
  "max_tokens": 1024,
  "messages": [
    {"role": "user", "content": "내 이름은 데이비드야"}
  ]
}
```

응답:

```
{"role": "assistant", "content": [{"type":"text","text":"반가워요, 데이비드!"}]}
```

이제 이어서 물어봅니다. 방금 대화는 서버가 기억하고 있을까요?

```
POST /v1/messages
{
  "messages": [
    {"role": "user", "content": "내 이름이 뭐라고?"}
  ]
}
```

```
{"content": [{"type":"text","text":"죄송하지만 이름을 알려주신 적이 없어요."}]}
```

**세션도, 대화 ID 도 없습니다.** 서버에는 이전 요청의 흔적이 전혀 남지 않습니다. 함수 하나를 호출한 것과 같고, 함수는 인자로 받은 것만 압니다.

> 이게 이 시리즈 전체를 관통하는 첫 번째 사실입니다.
> **LLM API 는 상태가 없는(stateless) 순수 함수에 가깝다.**

## 그럼 대화는 어떻게 이어지나 — 매번 전부 다시 보낸다

기억이 없다면 방법은 하나뿐입니다. **매 요청마다 지금까지의 대화 전체를 다시 보내는 것**입니다.

```
POST /v1/messages
{
  "messages": [
    {"role": "user",      "content": "내 이름은 데이비드야"},
    {"role": "assistant", "content": "반가워요, 데이비드!"},
    {"role": "user",      "content": "내 이름이 뭐라고?"}
  ]
}
```

```
{"content": [{"type":"text","text":"데이비드라고 하셨어요."}]}
```

기억하는 것처럼 보이지만, 실제로는 **클라이언트가 이력을 들고 있다가 통째로 다시 붙여 보낸** 것뿐입니다.

이 사실 하나에서 여러 가지가 따라 나옵니다.

- 대화가 길어질수록 **매 요청이 무거워집니다.** 토큰 비용이 대화 길이에 비례해 늘어나는 이유입니다.
- 그래서 같은 앞부분을 계속 다시 보내게 되고, 이걸 캐시하는 **prompt caching** 이 중요해집니다. (2편)
- 이력이 컨텍스트 윈도우를 넘기 직전이 되면 **요약해서 줄여야** 합니다. 그게 자동 압축(auto-compact)입니다. (2편)

## 파일은 누가 읽나 — 모델은 JSON 을 뱉을 뿐이다

두 번째 의문. 모델이 어떻게 내 파일을 읽을까요?

**못 읽습니다.** 모델이 할 수 있는 건 텍스트를 생성하는 것뿐입니다. 대신 이렇게 합니다.

요청에 "너는 이런 도구들을 쓸 수 있다"는 목록을 같이 보냅니다.

```
"tools": [
  {
    "name": "Read",
    "description": "Reads a file from the local filesystem.",
    "input_schema": {
      "type": "object",
      "properties": { "file_path": {"type": "string"} },
      "required": ["file_path"]
    }
  }
]
```

그러면 모델은 답변 대신 **"이 도구를 이 인자로 부르고 싶다"는 구조화된 블록**을 내놓습니다.

```
{"type": "tool_use", "id": "toolu_01A", "name": "Read",
 "input": {"file_path": "/app/auth.py"}}
```

여기까지가 모델이 하는 전부입니다. **파일을 여는 건 여러분 컴퓨터에서 도는 Claude Code 프로세스**입니다. 읽은 결과를 다시 대화에 붙여서 보냅니다.

```
{"role": "user", "content": [
  {"type": "tool_result", "tool_use_id": "toolu_01A",
   "content": "1\tdef login(...):\n2\t    ..."}
]}
```

> **핵심:** 모델은 "함수를 호출"하지 않습니다. **함수를 호출해 달라는 JSON 을 생성**할 뿐이고, 실제 실행·권한 확인·에러 처리는 전부 하네스 몫입니다. 5편에서 자세히 봅니다.

## 전체 그림

위의 두 가지를 합치면 Claude Code 의 뼈대가 나옵니다. 정말로 이게 전부입니다.

```python
messages = []

while True:
    messages.append(user_input())          # 사람이 입력

    while True:
        response = call_llm(               # 매번 전부 다시 보낸다
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )
        messages.append(response)

        if response.stop_reason != "tool_use":
            break                          # 할 말 끝 → 사람에게 턴을 넘긴다

        results = [run_tool(b) for b in response.tool_use_blocks]
        messages.append({"role": "user", "content": results})
```

안쪽 `while` 이 **agent loop** 입니다. 모델이 "도구를 쓰겠다"고 하면 실행하고 결과를 붙여서 다시 물어보고, 더 쓸 도구가 없으면 빠져나옵니다.

실제 Claude Code 도 구조상 이것과 같습니다. 번들에서 확인되는 실제 루프도 제너레이터 하나에 `while(!0)` — 즉 `while(true)` 입니다. 물론 그 주위에 권한, 훅, 압축, 병렬 실행, 서브에이전트가 붙어서 복잡해지는데, **그 붙어 있는 것들이 바로 이 시리즈의 내용**입니다.

## 이 시리즈에서 볼 것

| 편 | 주제 |
|---|---|
| 1편 | 엔터를 치면 무슨 일이 일어나는가 — 입력 파싱, `/` `!` `#` `@` |
| 2편 | 요청 바디 해부 — system 프롬프트, CLAUDE.md, 캐시, 압축 |
| 3편 | 응답 — SSE 스트리밍과 `stop_reason` |
| 4편 | Agent loop — 루프의 실체, 병렬 실행, 인터럽트 |
| 5편 | Tool — 도구 정의와 왕복, 권한 시스템 |
| 6편 | Hook — 하네스에 내 코드를 꽂는 자리 |
| 7편 | 서브에이전트 — 컨텍스트를 지키는 격리 |
| 8편 | 에이전트 종류 — 빌트인 에이전트 목록 |
| 9편 | Workflow 와 확장 표면 — Skill, 슬래시 커맨드, plan mode |

## 관찰 도구 3종 — 이 시리즈를 읽는 방법

이 시리즈는 "이렇다더라"로 쓰지 않았습니다. **전부 설치된 바이너리와 실제 요청을 직접 열어서 확인**했고, 여러분도 똑같이 확인할 수 있게 명령을 같이 적습니다. 먼저 도구 3개를 준비합시다.

### 도구 1. 세션 트랜스크립트 — 가장 쉽고 가장 많이 쓴다

Claude Code 는 모든 세션을 JSONL 로 디스크에 남깁니다. 이미 쌓여 있으니 지금 바로 볼 수 있습니다.

```bash
ls ~/.claude/projects/
```

프로젝트 경로의 `/` 를 `-` 로 바꾼 이름의 디렉터리가 보입니다. 그 안에 세션마다 `<uuid>.jsonl` 이 하나씩 있습니다.

한 줄이 곧 하나의 레코드입니다. 가장 최근 세션에서 대화 레코드만 뽑아봅시다.

```bash
f=$(ls -t ~/.claude/projects/*/*.jsonl | head -1)
jq -c 'select(.type=="user" or .type=="assistant") | {type, role: .message.role}' "$f" | head -3
```

```
{"type":"user","role":"user"}
{"type":"assistant","role":"assistant"}
{"type":"assistant","role":"assistant"}
```

어떤 종류의 레코드가 있는지 통째로 세어봅시다.

```bash
jq -r '.type' "$f" | sort | uniq -c | sort -rn
```

제 세션에서는 이렇게 나왔습니다. [관찰]

```
 159 attachment
  72 assistant
  37 user
  11 permission-mode
  11 mode
  ...
   7 system
```

`user` / `assistant` 가 실제 대화이고, 나머지는 UI 상태나 첨부 같은 **로컬 전용 레코드**입니다. 여기서 벌써 한 가지가 드러납니다 — **트랜스크립트에 있는 것이 전부 API 로 나가는 것은 아닙니다.** 1편에서 이 구분이 중요해집니다.

앞으로 편마다 이 파일에 `jq` 를 걸어 확인합니다.

### 도구 2. `--debug api` — 요청이 나가는 순간을 본다

```bash
claude --debug api -p "2+2는?"
```

`[API REQUEST] /v1/messages` 같은 줄이 stderr 로 흘러나옵니다. 어떤 요청이 몇 번 나가는지 감을 잡기 좋습니다.

### 도구 3. 로컬 싱크(sink) — 요청 바디를 통째로 캡처한다

가장 강력한 방법입니다. **`ANTHROPIC_BASE_URL` 을 내 컴퓨터의 작은 서버로 돌려놓고, 가짜 API 키로 Claude Code 를 실행**합니다. 그러면 진짜 요청 바디가 그대로 파일에 떨어집니다.

```bash
S=/tmp/cc-lab; mkdir -p $S/capture
cat > $S/sink.py <<'PY'
import http.server, json, os, gzip
OUT='/tmp/cc-lab/capture'; N=[0]
SSE=('event: message_start\ndata: {"type":"message_start","message":{"id":"msg_local","type":"message","role":"assistant","model":"m","content":[],"stop_reason":null,"stop_sequence":null,"usage":{"input_tokens":10,"output_tokens":1}}}\n\n'
     'event: content_block_start\ndata: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}\n\n'
     'event: content_block_delta\ndata: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"PONG"}}\n\n'
     'event: content_block_stop\ndata: {"type":"content_block_stop","index":0}\n\n'
     'event: message_delta\ndata: {"type":"message_delta","delta":{"stop_reason":"end_turn","stop_sequence":null},"usage":{"output_tokens":2}}\n\n'
     'event: message_stop\ndata: {"type":"message_stop"}\n\n')
class H(http.server.BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def log_message(self,*a): pass
    def do_POST(self):
        N[0]+=1
        ln=int(self.headers.get('content-length') or 0)
        raw=self.rfile.read(ln) if ln else b''
        if (self.headers.get('content-encoding') or '')=='gzip': raw=gzip.decompress(raw)
        # 자격증명은 저장하지 않는다
        hdrs={k:('<REDACTED>' if k.lower() in ('authorization','x-api-key') else v)
              for k,v in self.headers.items()}
        json.dump({'path':self.path,'headers':hdrs,'body':json.loads(raw)},
                  open(os.path.join(OUT,'req%02d.json'%N[0]),'w'), indent=1)
        b=SSE.encode(); self.send_response(200)
        self.send_header('content-type','text/event-stream')
        self.send_header('content-length',str(len(b)))
        self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        self.send_response(404); self.send_header('content-length','2')
        self.end_headers(); self.wfile.write(b'{}')
http.server.ThreadingHTTPServer(('127.0.0.1',8931),H).serve_forever()
PY
python3 $S/sink.py & sleep 1
```

이제 실험용 프로젝트를 하나 만들고, **가짜 키로** 실행합니다.

```bash
mkdir -p $S/lab && cd $S/lab && git init -q . \
  && echo x > note.txt && git add -A \
  && git -c user.email=a@b -c user.name=t commit -qm init

CLAUDE_CONFIG_DIR=$S/cfg ANTHROPIC_BASE_URL=http://127.0.0.1:8931 \
  ANTHROPIC_API_KEY=sk-ant-fake \
  claude -p "Reply with exactly: PONG" --model claude-haiku-4-5-20251001
```

캡처된 요청의 최상위 키를 봅시다.

```bash
jq '.body | keys' $S/capture/req02.json
```

```json
["context_management","max_tokens","messages","metadata","model","stream","system","thinking","tools"]
```

**이게 Claude Code 가 LLM 에게 보내는 전부입니다.** 2편에서 이 아홉 개를 하나씩 뜯어봅니다.

실험이 끝나면 서버를 꼭 내립니다.

```bash
pkill -f 'cc-lab/sink.py'
lsof -nP -iTCP:8931 -sTCP:LISTEN     # 아무것도 안 나와야 정상
```

> **두 가지 요령이 이 세팅의 핵심입니다.**
> - `CLAUDE_CONFIG_DIR=$S/cfg` — 설정 디렉터리를 새 경로로 지정하면 **내 플러그인·설정이 전혀 로드되지 않습니다.** 순수 builtin 상태를 관찰하려면 반드시 필요합니다.
> - `ANTHROPIC_API_KEY=sk-ant-fake` — 요청은 내 컴퓨터의 싱크에서 끝나므로 **진짜 키가 필요 없고, 밖으로 나가지도 않습니다.**

## 이 시리즈의 규칙 두 가지

**첫째, 버전을 고정합니다.** 이 글은 전부 **Claude Code 2.1.243** 기준입니다. 내부 구조는 버전마다 바뀝니다 — 실제로 이 조사 중에도 이전 버전에 있던 에이전트 하나가 사라진 것을 확인했습니다(8편). 여러분 버전을 먼저 확인하세요.

```bash
claude --version
ls -la ~/.local/share/claude/versions/
```

> **주의 두 가지.**
> 1. 앞으로 나오는 명령에서 `B=$(ls -d ~/.local/share/claude/versions/* | tail -1)` 은 **설치된 것 중 가장 최신**을 고릅니다. 여러 버전이 남아 있으면 제가 본 2.1.243 이 아닐 수 있습니다. 숫자가 저와 다르면 먼저 이걸 의심하세요. 특정 버전을 보려면 경로를 직접 적으세요 — `B=~/.local/share/claude/versions/2.1.243`
> 2. Claude Code 는 **알아서 업데이트됩니다.** 실제로 이 시리즈를 쓰는 동안 제 머신이 2.1.243 → 2.1.245 → 2.1.246 으로 올라갔습니다. 옛 버전은 파일로 남아 있어서 나중에도 대조할 수 있습니다(디렉터리가 아니라 **단일 실행 파일**입니다).
>
> 3. **그리고 중요한 변화가 하나 있습니다.** 2.1.246 부터는 JS 소스의 일부가 **바이트코드로 컴파일**되어, 이 시리즈가 쓰는 `strings` 추출이 예전만큼 듣지 않습니다. [관찰]
>
>    ```bash
>    B3=~/.local/share/claude/versions/2.1.243
>    B6=~/.local/share/claude/versions/2.1.246
>    ls -l "$B3" "$B6" | awk '{print $5, $NF}'      # 361MB vs 230MB — 더 작아졌다
>    LC_ALL=C grep -ac 'function aMe()' "$B3"       # 1  ← 평문으로 있음
>    LC_ALL=C grep -ac 'function aMe()' "$B6"       # 0  ← 사라짐
>    LC_ALL=C grep -ac 'CLAUDE_CODE_FORK_SUBAGENT' "$B6"   # 4  ← 문자열 상수는 그대로
>    ```
>
>    **함수 본문은 안 보이지만 문자열 상수는 여전히 보입니다.** 그래서 이 시리즈의 코드 인용은 전부 **2.1.243**(평문 JS 가 남은 마지막 버전) 기준이고, 동작 확인은 최신 버전에서 해도 됩니다. 여러분 버전이 더 높아서 `grep` 이 0 을 뱉는다면, **기능이 없어진 게 아니라 안 보이게 된 것**일 수 있습니다.

**둘째, 증거의 등급을 표시합니다.** 문장 끝에 이렇게 붙습니다.

- **[관찰]** — 직접 실행해서 눈으로 본 것
- **[문서]** — 공식 문서에 있는 것
- **[추론]** — 정황으로 미루어 짐작한 것

**[추론]** 이 붙은 문장은 틀릴 수 있습니다. 그렇게 표시하는 게 정직하다고 생각합니다.

## 정리

- LLM API 는 **상태가 없습니다.** 대화 이력은 매 요청마다 클라이언트가 통째로 다시 보냅니다.
- 모델은 **파일을 읽지 못합니다.** "이 도구를 부르고 싶다"는 JSON 을 생성할 뿐이고, 실행은 하네스가 합니다.
- 그래서 Claude Code 의 뼈대는 **`while` 루프 하나** 입니다. `stop_reason` 이 `tool_use` 인 동안 돌고, 아니면 빠져나옵니다.
- 이 시리즈의 모든 주장은 **트랜스크립트 · `--debug api` · 로컬 싱크** 셋 중 하나로 직접 확인할 수 있습니다.

다음 편에서는 루프의 입구부터 봅니다. 여러분이 프롬프트를 치고 **엔터를 누른 그 순간**, 첫 글자가 무엇이냐에 따라 완전히 다른 일이 벌어집니다.

> 다음 편: [1편. 엔터를 치면 무슨 일이 일어나는가](./01-prompt-to-messages.md)
