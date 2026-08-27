# 11편(캡스톤). 직접 만들어보기 — 150줄짜리 미니 Claude Code

> 시리즈: Claude Code 내부 구조 (builtin 기준, v2.1.243)
> 이 편에서 하는 것: 지금까지 본 구조를 **실제로 도는 149 줄 파이썬**으로 만들어봅니다. 그리고 일부러 부딪혀서, 시리즈에서 본 장치들이 **왜 있는지**를 손으로 이해합니다.

0편의 뼈대를 네 줄로 줄이면 이렇습니다.

```python
while True:
    response = call_llm(messages, tools)
    if response.stop_reason != "tool_use": break
    messages.append(run_tools(response))
```

(0편의 원본은 사람 입력을 받는 바깥 루프까지 있는 16 줄짜리입니다. 여기서는 안쪽 루프만 남겼습니다.)

아홉 편을 지나 이 네 줄에 무엇이 붙어 있는지 다 봤습니다. 이제 **정말로 네 줄인지** 확인해봅시다.

## 만들 것과 안 만들 것

**만들 것** — 파일을 읽고 쓰고 명령을 실행하는, 진짜로 도는 에이전트.

**안 만들 것** — 스트리밍(3편), 권한(5편), 훅(6편), 압축(2편), 병렬 툴 실행(4편), 터미널 UI. 전부 뺍니다.

> **왜 빼냐면**, 빼고 만들어봐야 **왜 필요한지** 알게 되기 때문입니다. 이 편의 뒷부분은 하나씩 부딪혀보는 시간입니다.

## 코드

> **아래 다섯 블록을 순서대로 이어붙이면 `mini_cc.py` 가 됩니다.** 사이에 빈 줄 하나씩 넣으면 약 150 줄이 됩니다.

### 0. 준비

```python
#!/usr/bin/env python3
"""mini_cc.py — 150줄짜리 미니 Claude Code

사용법:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 mini_cc.py "이 디렉터리에 뭐가 있는지 알려줘"
"""
import json, os, subprocess, sys, urllib.request

BASE  = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
KEY   = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = os.environ.get("MINI_CC_MODEL", "claude-haiku-4-5-20251001")

SYSTEM = (
    "You are a small coding assistant running in a terminal. "
    "Use the tools to inspect and modify files. "
    "When the task is done, reply with a short plain-text summary and stop."
)
```

`SYSTEM` 이 짧다는 데 주목하세요. 2편에서 본 진짜 시스템 프롬프트는 블록 3 개짜리 배열이고, 그중 **본문 블록만 27,824 자**였습니다. 우리 건 세 줄입니다.

### 2. 툴 정의 — 세 키뿐이다

```python
# ── 1. 툴 정의 — 모델에게 보내는 것은 이 세 키뿐이다 (5편) ──────────────
TOOLS = [
    {
        "name": "Read",
        "description": "Read a UTF-8 text file. Returns the content with line numbers.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File path"}},
            "required": ["path"],
        },
    },
    {
        "name": "Write",
        "description": "Write text to a file, creating or overwriting it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "Bash",
        "description": "Run a shell command and return its stdout and stderr.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
]
```

5편에서 본 그대로 **`name` / `description` / `input_schema`** 뿐입니다. 5편에서 강조했듯 **`description` 이 곧 프롬프트**입니다. 여기 적은 한 줄이 그 툴의 사용법 안내 전부입니다.

### 3. 툴 실행 — 모델이 아니라 이 프로세스가 한다

```python
# ── 2. 툴 실행 — 모델이 아니라 '이 프로세스'가 한다 (0편·5편) ──────────
def tool_read(args):
    with open(args["path"], encoding="utf-8") as f:
        lines = f.read().splitlines()
    return "\n".join(f"{i:6d}\t{l}" for i, l in enumerate(lines, 1))

def tool_write(args):
    with open(args["path"], "w", encoding="utf-8") as f:
        f.write(args["content"])
    return f"Wrote {len(args['content'])} bytes to {args['path']}"

def tool_bash(args):
    p = subprocess.run(args["command"], shell=True, capture_output=True,
                       text=True, timeout=60)
    out = (p.stdout or "") + (p.stderr or "")
    return f"(exit {p.returncode})\n{out}".strip()

HANDLERS = {"Read": tool_read, "Write": tool_write, "Bash": tool_bash}

def run_tool(block):
    """tool_use 블록 하나 → tool_result 블록 하나.
    실패해도 예외를 던지지 않는다. is_error 를 달아 대화로 돌려보낸다 (5편)."""
    result = {"type": "tool_result", "tool_use_id": block["id"]}
    handler = HANDLERS.get(block["name"])
    if handler is None:
        result["content"] = f"No such tool: {block['name']}"
        result["is_error"] = True
        return result
    try:
        result["content"] = handler(block["input"])
    except Exception as e:
        result["content"] = f"{type(e).__name__}: {e}"
        result["is_error"] = True
    return result
```

**`run_tool` 이 예외를 던지지 않는 것**이 핵심입니다. 실패해도 `is_error` 를 달아서 **대화로 돌려보냅니다.** 5편에서 "에러는 예외가 아니라 대화"라고 했던 게 이 세 줄입니다.

### 4. API 호출 — 매번 전부 보낸다

```python
# ── 3. API 호출 — 상태가 없으므로 '매번 전부' 보낸다 (0편·2편) ─────────
def call_llm(messages):
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 4096,
        "system": SYSTEM,
        "tools": TOOLS,
        "messages": messages,     # ← 지금까지의 대화 전체
    }).encode()
    req = urllib.request.Request(
        BASE + "/v1/messages", data=body, method="POST",
        headers={"content-type": "application/json",
                 "x-api-key": KEY,
                 "anthropic-version": "2023-06-01"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        # 에러 본문에 진짜 이유가 들어 있다. urllib 은 이걸 안 보여준다.
        sys.exit(f"API {e.code}: {e.read().decode(errors='replace')}")
```

`messages` 를 통째로 넣는 저 한 줄이 0편의 "LLM 은 상태가 없다"의 전부입니다. 스트리밍도 안 씁니다(`stream` 키가 없죠). 3편에서 본 SSE 조립을 건너뛰려고 일부러 뺐습니다.

### 5. 루프

```python
# ── 4. Agent loop — 이게 전부다 (4편) ──────────────────────────────────
def run_turn(messages, max_turns=20):
    for turn in range(1, max_turns + 1):
        reply = call_llm(messages)

        # assistant 응답을 이력에 그대로 append
        messages.append({"role": "assistant", "content": reply["content"]})

        for b in reply["content"]:
            if b["type"] == "text" and b["text"].strip():
                print(f"\n🤖 {b['text'].strip()}")

        # ★ stop_reason 이 루프를 계속 돌릴지 정한다 (3편)
        if reply.get("stop_reason") != "tool_use":
            return reply.get("stop_reason")

        calls = [b for b in reply["content"] if b["type"] == "tool_use"]
        results = []
        for b in calls:
            print(f"   ⚙  {b['name']}({json.dumps(b['input'], ensure_ascii=False)[:70]})")
            results.append(run_tool(b))

        # tool_result 는 'user' 역할로 들어간다 — 사람이 쓴 게 아닌데도
        messages.append({"role": "user", "content": results})

    print("\n⚠️  max_turns 도달 — 루프를 강제 종료합니다 (4편의 가드)")
    return "max_turns"

def main():
    if not KEY:
        sys.exit("ANTHROPIC_API_KEY 를 설정하세요.")
    prompt = " ".join(sys.argv[1:]) or input("> ")
    messages = [{"role": "user", "content": prompt}]
    stop = run_turn(messages)
    print(f"\n── 종료: stop_reason={stop}, 메시지 {len(messages)}개 ──")

if __name__ == "__main__":
    main()
```

**이게 4편 전체입니다.** `stop_reason` 을 보고 계속할지 말지 정하고, 툴 결과를 `user` 역할로 붙여서 다시 부릅니다.

> `messages.append({"role": "user", "content": results})` — 툴 결과가 **`user` 로 들어간다**는 게 처음엔 이상합니다. 사람이 쓴 게 아닌데요. 1편에서 `promptSource: "system"` 이 1,417 건이었던 것, 7편의 `<task-notification>`, 6편의 훅 주입 — 전부 같은 이야기입니다. **대화의 `user` 자리에는 사람 말고도 여러 발신자가 있습니다.**

## 키 없이 먼저 돌려보기

API 키를 쓰기 전에, 0편의 로컬 싱크 방식으로 **가짜 API** 를 만들어 루프만 검증합시다.

```python
# fake_api.py — 2턴 시나리오를 되돌려주는 가짜 서버
import http.server, json
N = [0]
def reply(n, body):
    if n == 1:
        return {"content":[{"type":"text","text":"파일을 세어볼게요."},
                          {"type":"tool_use","id":"toolu_1","name":"Bash",
                            "input":{"command":"ls -1 | wc -l"}}],
                "stop_reason":"tool_use"}
    last = body["messages"][-1]
    got = last["content"][0]["content"]
    return {"content":[{"type":"text","text":f"결과를 받았습니다: {got.strip()}"}],
            "stop_reason":"end_turn"}
class H(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self,*a): pass
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("content-length") or 0)))
        N[0] += 1
        print(f"[sink] 요청 {N[0]}: messages={len(body['messages'])}개, tools={len(body['tools'])}개")
        out = json.dumps({"id":"m","type":"message","role":"assistant",**reply(N[0],body)}).encode()
        self.send_response(200); self.send_header("content-type","application/json")
        self.send_header("content-length",str(len(out))); self.end_headers(); self.wfile.write(out)
http.server.ThreadingHTTPServer(("127.0.0.1",8951),H).serve_forever()
```

```bash
python3 -u fake_api.py > sink.log 2>&1 &
ANTHROPIC_BASE_URL=http://127.0.0.1:8951 ANTHROPIC_API_KEY=fake \
  python3 mini_cc.py "이 디렉터리에 파일이 몇 개야?"
pkill -f fake_api.py
```

실제 출력입니다. [관찰]

```
🤖 파일을 세어볼게요.
   ⚙  Bash({"command": "ls -1 | wc -l"})

🤖 결과를 받았습니다: (exit 0)
       4

── 종료: stop_reason=end_turn, 메시지 4개 ──
```

(`4` 는 제가 돌린 디렉터리의 파일 수라 여러분 값은 다릅니다. 반면 마지막 줄의 **"메시지 4개"** 는 **항상 같습니다** — `user` → `assistant` → `user`(tool_result) → `assistant` 로 4 개니까요.)

**돕니다.** 149 줄로 툴을 부르고, 실행하고, 결과를 받아 대답까지 했습니다.

### 그리고 이게 핵심 증거입니다

싱크가 본 것을 보세요.

```bash
cat sink.log
```

```
[sink] 요청 1: messages=1개, tools=3개
[sink] 요청 2: messages=3개, tools=3개
```
[관찰]

**요청 1 은 메시지 1 개, 요청 2 는 3 개.** 서버는 아무것도 기억하지 않았고, 우리 클라이언트가 이력을 통째로 다시 보냈습니다. 0편에서 말로만 했던 것을 **이제 눈으로 봤습니다.**

`tools=3` 이 매번 반복되는 것도 보이시죠. **툴 정의도 매 요청마다 다시 전송됩니다.** 2편에서 본 deferred tools 와 프롬프트 캐싱이 바로 이 비용을 줄이려는 장치였습니다.

## 진짜로 돌리기

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 mini_cc.py "이 폴더에서 가장 큰 파일 3개를 찾아서 sizes.txt 에 적어줘"
```

진짜 모델은 `Bash` 로 파일을 찾고, `Write` 로 결과를 쓰고, 요약을 돌려줄 것입니다. **여러분이 방금 만든 것으로요.** [추론] — 이 편의 실행 검증은 전부 가짜 API 로 했습니다. 진짜 키로 돌린 결과는 싣지 않았습니다.

## 이제 일부러 부딪혀봅시다

여기부터가 진짜입니다. 뺀 것들이 **왜 필요했는지**를 직접 겪어봅니다.

### 부딪힘 1 — 컨텍스트가 터진다

```bash
python3 mini_cc.py "이 저장소의 모든 .py 파일을 하나씩 Read 해서 요약해줘"
```

`messages` 가 걷잡을 수 없이 커지다가 어느 순간 API 가 거부합니다. [추론]

> **실제로는 `max_turns` 가 먼저 터질 가능성이 높습니다.** 우리 루프는 20 턴에서 멈추니까요(4편의 가드). 컨텍스트 한계까지 가려면 큰 파일이 꽤 많이 필요합니다. 둘 중 무엇이 먼저 오든, **한계가 있다는 것**이 요점입니다.

```
API 400: {"type": "error", "error": {"type": "invalid_request_error",
          "message": "prompt is too long: 1252025 tokens > 1000000 maximum"}}
```

> **`call_llm` 의 `except urllib.error.HTTPError` 가 없으면 이 메시지를 못 봅니다.** urllib 은 `HTTPError: HTTP Error 400: Bad Request` 만 던지고 **본문을 안 보여줍니다.** 진짜 이유는 본문에 있죠. 처음 만들 때 제가 실제로 빠뜨렸던 부분이라 코드에 넣어뒀습니다.

**여기서 2편이 회수됩니다.** 대화를 요약해서 갈아끼우는 자동 압축이 왜 있는지, 왜 그게 2 분씩 걸리는 비싼 작업인지. 그리고 왜 손실 압축인지도요 — 요약하면 세부는 사라집니다.

> 직접 붙여보고 싶다면: `messages` 의 총 길이를 재다가 임계값을 넘으면, 앞부분을 LLM 에게 요약시켜 한 개의 메시지로 바꿔치기하면 됩니다. 30 줄이면 됩니다. **어디까지 요약하고 무엇을 남길지**가 어렵다는 걸 바로 알게 될 겁니다.

### 부딪힘 2 — `Edit` 을 붙이면 남의 변경을 덮어쓴다

`Write` 는 파일을 통째로 덮어씁니다. 부분 수정을 하려고 `Edit` 툴을 추가해봅시다.

```python
def tool_edit(args):
    with open(args["path"], encoding="utf-8") as f:
        text = f.read()
    if args["old"] not in text:
        raise ValueError("old string not found")
    with open(args["path"], "w", encoding="utf-8") as f:
        f.write(text.replace(args["old"], args["new"], 1))
    return "edited"

# 핸들러 등록을 빠뜨리면 모델은 이 툴을 부를 수 없습니다
HANDLERS["Edit"] = tool_edit
TOOLS.append({
    "name": "Edit",
    "description": "Replace the first occurrence of `old` with `new` in a file.",
    "input_schema": {
        "type": "object",
        "properties": {"path": {"type": "string"},
                       "old": {"type": "string"},
                       "new": {"type": "string"}},
        "required": ["path", "old", "new"],
    },
})
```

잘 도는 것 같습니다. 그런데 이렇게 해보세요.

1. 모델에게 파일을 `Read` 시킨다
2. **여러분이 에디터에서 그 파일을 고친다**
3. 모델에게 `Edit` 을 시킨다

모델은 **자기가 읽었던 옛 내용**을 기준으로 고칩니다. 그래서 `old string not found` 로 **시끄럽게 실패**합니다. 여기까지는 괜찮습니다.

문제는 **그다음**입니다. 실패를 본 모델은 흔히 이렇게 판단합니다 — "Edit 이 안 되네, 그럼 `Write` 로 파일을 통째로 다시 쓰자." 그리고 **자기 기억 속의 옛 내용으로 파일을 덮어씁니다.** 여러분의 변경은 그때 사라집니다.

그리고 실패하지 않고 **엉뚱한 곳을 고치는** 경우도 있습니다. `replace(old, new, 1)` 은 **첫 번째** 일치만 바꾸므로, 같은 문자열이 파일에 두 번 나오면 모델이 의도한 자리가 아닌 곳이 바뀝니다.

> **한 번의 `Edit` 이 조용히 되돌리는 게 아닙니다.** `Edit` 은 대개 정직하게 실패합니다. 위험한 건 두 가지입니다 — **실패가 `Write` 로 이어지는 연쇄**, 그리고 **첫 일치 오적중**. 5편이 "엉뚱한 곳을 고치거나 남의 변경을 덮어씁니다"라고 했던 게 정확히 이 둘입니다.
>
> 그래서 방어를 `Edit` 안에 두면 늦습니다 — **읽은 시점 자체를 기록**해야 합니다.

**여기서 5편이 회수됩니다.** Claude Code 가 이런 문자열을 갖고 있던 이유입니다.

```
"File has been modified since read, either by the user or by a linter.
 Read it again before attempting to write it."
```

읽은 시각을 기록해두고 `mtime` 과 비교하면 됩니다. **10 줄이면 되는데, 없으면 데이터가 사라집니다.**

### 부딪힘 3 — 탐색이 컨텍스트를 다 먹는다

```bash
python3 mini_cc.py "인증 관련 코드가 어디 있는지 찾아줘"
```

모델이 파일 수십 개를 열어보고 답은 세 줄입니다. [추론] 그런데 **마흔 개의 내용이 전부 `messages` 에 남았고**, 이후 모든 요청에 따라다닙니다.

**여기서 7편이 회수됩니다.** 그리고 이건 25 줄로 고칠 수 있습니다.

## 서브에이전트 — 25줄

```python
def tool_agent(args):
    """서브에이전트. 격리의 정체는 이 한 줄 — 부모 이력을 안 넘기고 새 배열로 시작한다."""
    sub = [{"role": "user", "content": args["prompt"]}]   # ← 부모 messages 를 안 준다
    print("   ┌─ 서브에이전트 시작")
    run_turn(sub, max_turns=10)                            # ← 같은 루프 코드를 그대로 재사용
    print("   └─ 서브에이전트 종료")
    for m in reversed(sub):                                # 마지막 텍스트만 부모에게
        if m["role"] == "assistant":
            for b in m["content"]:
                if b["type"] == "text" and b["text"].strip():
                    return b["text"].strip()
    return "(no result)"

HANDLERS = {"Read": tool_read, "Write": tool_write,
            "Bash": tool_bash, "Agent": tool_agent}
```

툴 정의도 하나 추가합니다.

```python
{
    "name": "Agent",
    "description": ("Delegate a self-contained subtask to a fresh assistant that "
                    "shares none of this conversation. Brief it fully. "
                    "You get back only its final answer."),
    "input_schema": {
        "type": "object",
        "properties": {"prompt": {"type": "string"}},
        "required": ["prompt"],
    },
},
```

**7편에서 본 격리 모델의 정체가 이것입니다.** 대단한 장치가 아니라 **새 리스트 하나**입니다.

- `sub = [...]` — 부모의 `messages` 를 안 넘깁니다. 그래서 자식은 부모 대화를 모릅니다.
- `run_turn(sub, ...)` — **같은 루프 함수를 그대로 씁니다.** 4편에서 "메인과 서브에이전트는 같은 코드"라고 했던 그것입니다.
- 마지막 텍스트만 반환 — 툴 출력 원문은 부모에게 안 갑니다.

### 격리가 진짜로 되는지 확인

가짜 API 를 4턴 시나리오로 바꿔 확인했습니다. 요청 번호로 응답을 정해주는 스크립트입니다.

```python
# fake_api2.py — 부모 1턴 → 자식 2턴 → 부모 1턴
import http.server, json
N=[0]
def reply(n, body):
    if n == 1:   # 부모: 위임 결정
        return {"content":[{"type":"text","text":"서브에이전트에게 맡기겠습니다."},
                {"type":"tool_use","id":"t1","name":"Agent",
                 "input":{"prompt":"Count the files in the current directory and report just the number."}}],
                "stop_reason":"tool_use"}
    if n == 2:   # 자식 1턴: 새 대화로 시작
        return {"content":[{"type":"tool_use","id":"t2","name":"Bash",
                 "input":{"command":"ls -1 | wc -l"}}], "stop_reason":"tool_use"}
    if n == 3:   # 자식 2턴: 결론
        return {"content":[{"type":"text","text":"6개입니다."}], "stop_reason":"end_turn"}
    return {"content":[{"type":"text","text":"서브에이전트가 6개라고 보고했습니다."}],
            "stop_reason":"end_turn"}
class H(http.server.BaseHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    def log_message(self,*a): pass
    def do_POST(self):
        b=json.loads(self.rfile.read(int(self.headers.get("content-length") or 0)))
        N[0]+=1
        who = "부모" if N[0] in (1,4) else "자식"      # 시나리오가 고정이라 번호로 판정
        first = b["messages"][0]["content"]
        if isinstance(first,str): first=first[:40]
        print(f"[sink] 요청{N[0]} ({who}): messages={len(b['messages'])}개  첫메시지={first!r}")
        o=json.dumps({"id":f"m{N[0]}","type":"message","role":"assistant",**reply(N[0],b)}).encode()
        self.send_response(200); self.send_header("content-type","application/json")
        self.send_header("content-length",str(len(o))); self.end_headers(); self.wfile.write(o)
http.server.ThreadingHTTPServer(("127.0.0.1",8952),H).serve_forever()
```

```bash
python3 -u fake_api2.py > sink2.log 2>&1 &
ANTHROPIC_BASE_URL=http://127.0.0.1:8952 ANTHROPIC_API_KEY=fake \
  python3 mini_cc2.py "파일 몇 개야?"
pkill -f fake_api2.py; cat sink2.log
```

실제 출력입니다. [관찰]

```
🤖 서브에이전트에게 맡기겠습니다.
   ⚙  Agent({"prompt": "Count the files in the current directory and report just t)
   ┌─ 서브에이전트 시작
   ⚙  Bash({"command": "ls -1 | wc -l"})

🤖 6개입니다.
   └─ 서브에이전트 종료

🤖 서브에이전트가 6개라고 보고했습니다.
```

그리고 싱크가 본 것입니다.

```
[sink] 요청1 (부모): messages=1개  첫메시지='파일 몇 개야?'
[sink] 요청2 (자식): messages=1개  첫메시지='Count the files in the current directory'
[sink] 요청3 (자식): messages=3개  첫메시지='Count the files in the current directory'
[sink] 요청4 (부모): messages=3개  첫메시지='파일 몇 개야?'
```

**요청 2 를 보세요.** 자식의 첫 메시지가 `'파일 몇 개야?'` 가 아니라 브리핑입니다. **자식은 부모가 무슨 질문을 받았는지 모릅니다.**

**요청 4 를 보세요.** 부모의 메시지는 3 개뿐입니다. 자식이 실행한 `ls -1 | wc -l` 의 출력은 **부모 컨텍스트에 한 글자도 안 들어갔습니다.**

> 7편에서 실측했던 그 장면입니다 — 자식이 122,826 토큰을 쓰고 부모에겐 `"Acknowledged."` 만 돌아왔던 것. 규모만 다르지 **원리는 방금 여러분이 쓴 25 줄과 같습니다.**

## 안 만든 것 — 정직하게

이 174 줄과 진짜 Claude Code 사이에는 이런 것들이 있습니다.

| 빠진 것 | 어디서 다뤘나 | 난이도 |
|---|---|---|
| 스트리밍(SSE) + 스트리밍 중 툴 디스패치 | 3·4편 | 동시성 설계가 까다로움 |
| 권한 시스템 | 5편 | 그 자체로 하나의 프로젝트 |
| 훅 | 6편 | 31 개 이벤트 |
| 자동 압축 | 2편 | **무엇을 버릴지가 정답 없음** |
| `Edit` 의 파일 상태 추적 | 5편 | **의외의 최대 난관** |
| 병렬 툴 실행 | 4편 | 스케줄러 2 개 |
| 프롬프트 캐싱 | 2편 | 어디에 브레이크포인트를 둘지 |
| 서브에이전트 중첩 깊이 제한 | 7편 | 우리 자식은 `Agent` 를 또 부를 수 있습니다 (무한 재귀) |
| 터미널 UI | — | 실제 코드의 상당 부분 |
| 에러 분류와 재시도 | 3편 | 최대 10 회 지수 백오프 |

> **집에서 만든 에이전트가 실패하는 이유는 루프를 잘못 짜서가 아닙니다.** 루프는 방금 보셨듯 스무 줄입니다. 실패는 **툴 설명을 스펙처럼 쓰고**(프롬프트가 아니라), **컨텍스트를 아끼지 않고**, **에러를 예외로 던져버려서** 일어납니다. 이 시리즈가 실제로 가르친 게 그 세 가지입니다.

## 정리

- Claude Code 의 뼈대는 **정말로 while 루프 하나**입니다. 149 줄로 도는 걸 확인했습니다.
- 가짜 API 의 로그가 **"매번 전부 다시 보낸다"** 를 눈으로 증명했습니다 — 요청 1 은 1 개, 요청 2 는 3 개.
- **서브에이전트 격리는 새 리스트 하나**입니다. 25 줄이면 되고, 자식은 부모 대화를 못 보고 부모는 자식의 툴 출력을 못 봅니다.
- 뺀 것들(압축·파일 상태 추적·권한)은 **부딪혀보면 왜 있는지 알게 됩니다.** 특히 `Edit` 의 상태 추적은 없으면 **데이터가 사라집니다.**

여기까지가 시즌 1 입니다. 처음에 "마법 같다"고 했던 것이, 이제 **여러분이 짤 수 있는 루프와 JSON** 으로 보이면 성공입니다.

다음 시즌은 **멀티에이전트**입니다. 방금 25 줄로 만든 서브에이전트를 열 개 돌리려면 무엇이 필요한지 — 그리고 **언제 그게 오히려 손해인지** 를 실측으로 봅니다.

> 이전 편: [부록. `~/.claude` 안내 지도](./10-claude-dir.md)
> 시리즈 처음: [0편. 프롤로그 — Claude Code는 결국 while 루프 하나다](./00-prologue.md)
