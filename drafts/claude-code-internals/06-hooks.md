# 6편. Hook — 하네스에 내 코드를 꽂는 자리

> 시리즈: Claude Code 내부 구조 (builtin 기준, v2.1.243)
> 이 편에서 배우는 것: 훅 이벤트가 실제로 **31 개**라는 것, stdin/stdout 계약, exit code 2 의 특별한 의미, 그리고 훅 출력이 대화의 **어느 레코드**로 들어가는지.

2편에서 이런 실험을 했습니다.

```bash
{"hooks":{"UserPromptSubmit":[{"hooks":[{"type":"command","command":"printf 'HOOK_SAW_PROMPT_12345'"}]}]}}
```

그러자 셸 스크립트의 표준출력이 모델의 컨텍스트에 그대로 들어갔습니다. 이번 편은 그 메커니즘 전체입니다.

## 훅이란 무엇인가

한 문장으로: **하네스가 정해진 지점에서 내 프로그램을 실행하고, 그 결과로 동작을 바꾸는 것.**

지금까지 본 루프에는 여러 지점이 있었습니다. 프롬프트가 들어올 때, 툴을 실행하기 직전, 실행한 직후, 턴이 끝나려 할 때. **그 지점마다 내 스크립트를 끼울 수 있습니다.**

중요한 건 훅이 **관찰만 하는 게 아니라는** 점입니다. 툴 실행을 막을 수도 있고, 턴이 끝나는 것도 막을 수 있습니다.

## 이벤트는 31 개다

블로그 글에서 흔히 보는 목록은 아홉 개쯤입니다. `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Notification`, `Stop`, `SubagentStop`, `PreCompact`, `SessionEnd`.

**실제로는 31 개입니다.** 바이너리에서 두 군데(zod 스키마 선언, 런타임 리터럴)를 각각 뽑아 교차검증할 수 있습니다.

```bash
B=$(ls -d ~/.local/share/claude/versions/* | tail -1)
LC_ALL=C strings -n 4 "$B" > /tmp/cc.strings
python3 - <<'PY'
import re
S=open('/tmp/cc.strings',errors='ignore').read()
schema=sorted(set(re.findall(r'hook_event_name:\w+\("([A-Za-z]+)"\)',S)))
lit   =sorted(set(re.findall(r'hook_event_name:"([A-Za-z]+)"',S)))
print(len(schema), len(lit), schema==lit)
print(schema)
PY
```

```
31 31 True
```

두 목록이 완전히 일치합니다. [관찰] 분류하면 이렇습니다.

| 분류 | 이벤트 |
|---|---|
| 세션 | `SessionStart` `SessionEnd` `Setup` |
| 턴 | `UserPromptSubmit` `UserPromptExpansion` `Stop` `StopFailure` |
| 툴 | `PreToolUse` `PostToolUse` `PostToolUseFailure` `PostToolBatch` `PermissionRequest` `PermissionDenied` |
| 서브에이전트/팀 | `SubagentStart` `SubagentStop` `TeammateIdle` `TaskCreated` `TaskCompleted` |
| 컨텍스트/표시 | `PreCompact` `PostCompact` `MessageDisplay` `Notification` |
| 반응형 | `CwdChanged` `FileChanged` `DirectoryAdded` `ConfigChange` `InstructionsLoaded` |
| MCP | `Elicitation` `ElicitationResult` |
| Worktree | `WorktreeCreate` `WorktreeRemove` |

> 이 편은 드물게도 **공식 문서와 설치본이 정확히 일치**합니다. [문서]+[관찰] 다른 편들에서 문서와 실제가 어긋난 걸 여럿 봤으니, 이런 경우도 있다는 걸 짚어둡니다.

`FileChanged`, `CwdChanged` 같은 **반응형** 이벤트가 있다는 게 흥미롭습니다. 모델의 턴과 무관하게 파일이 바뀌면 발화합니다.

## 설정 모양

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [
          { "type": "command",
            "command": "/abs/path/my-hook.sh",
            "timeout": 10 }
        ] }
    ]
  }
}
```

`type` 은 다섯 가지입니다. [관찰]

| type | 무엇 |
|---|---|
| `command` | 셸 명령 실행 (가장 흔함) |
| `prompt` | LLM 을 불러서 판단 (`$ARGUMENTS` 에 훅 입력 JSON 이 들어감) |
| `mcp_tool` | MCP 툴 호출 |
| `http` | HTTP 요청 |
| `agent` | 서브에이전트 실행 |

핸들러의 주요 필드입니다. 바이너리에 박힌 설명 원문 기준입니다. [관찰]

| 필드 | 의미 |
|---|---|
| `command` | 실행할 셸 명령 |
| `args` | exec 형태 인자 배열. **셸 파서를 안 거치므로** 따옴표·`$`·백틱이 있는 경로도 안전 |
| `timeout` | **초 단위** (밀리초 아님!) |
| `once` | true 면 한 번 실행하고 제거됨 |
| `async` | true 면 백그라운드에서 돌고 블로킹하지 않음 |
| `asyncRewake` | 백그라운드로 돌되 **exit 2 로 끝나면 모델을 깨움** |
| `statusMessage` | 훅이 도는 동안 스피너에 표시할 문구 |

> **함정 1: `timeout` 은 초입니다.** `"timeout": 5000` 이라고 쓰면 5 초가 아니라 **83 분**입니다.
>
> **함정 2: `command` 는 셸을 거칩니다.** 경로에 공백이나 `$` 가 있으면 깨집니다. 안전하게 하려면 `args` 배열 형태를 쓰세요.

### `matcher` 가 비교하는 대상은 이벤트마다 다르다

여기가 가장 헷갈리는 지점입니다. `"matcher": "Bash"` 는 **툴 이벤트에서만** 의미가 있습니다. [관찰]

| 이벤트 | matcher 가 비교하는 필드 | 값 예시 |
|---|---|---|
| `PreToolUse` / `PostToolUse` / `PermissionRequest` | `tool_name` | `Bash`, `Edit\|Write` |
| `SessionStart` | `source` | `startup`, `resume`, `clear`, `compact`, `fork` |
| `SubagentStart` / `SubagentStop` | `agent_type` | |
| `PreCompact` | `trigger` | `manual`, `auto` |
| `Setup` | `trigger` | `init`, `maintenance` |
| `Notification` | `notification_type` | |
| `ConfigChange` | `source` | `user_settings`, `project_settings`, … |

> **`SessionStart` 에 `"matcher": "Bash"` 를 써도 조용히 아무 일도 안 일어납니다.** 에러가 아니라 그냥 `startup` 과 비교해서 안 맞을 뿐입니다. 훅이 안 도는 원인 1 순위입니다.

특수문자가 들어가면 **정규식**으로 해석됩니다. `"^Notebook"`, `"mcp__memory__.*"` 같은 식입니다. [문서]

## 계약 (1) — stdin 으로 오는 것

훅 스크립트는 **표준입력으로 JSON 한 덩어리**를 받습니다. 모든 이벤트에 공통인 필드입니다. [관찰]

```json
{ "session_id": "23d7457f-…",
  "transcript_path": "/Users/…/projects/<slug>/<id>.jsonl",
  "cwd": "/private/tmp/…",
  "hook_event_name": "PreToolUse" }
```

`transcript_path` 가 들어 있다는 게 재밌습니다. **훅에서 지금까지의 대화 전체를 읽을 수 있습니다.**

`PreToolUse` 의 실측 페이로드 전문입니다. [관찰]

```json
{ "session_id": "23d7457f-b6e6-446a-93b4-194e9e3f5dbf",
  "transcript_path": "/Users/iamslash/.claude/projects/…/23d7457f-….jsonl",
  "cwd": "/private/tmp/…/hooklab",
  "prompt_id": "5fe60c06-e034-49af-937e-72035d24baf1",
  "permission_mode": "default",
  "effort": {"level":"xhigh"},
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {"command":"echo hello-hooks","description":"Echo hello-hooks"},
  "tool_use_id": "toolu_019SJN3ArJvUFTffZevPaRdo" }
```

`PostToolUse` 는 여기에 결과가 붙습니다. [관찰]

```json
{ …,
  "hook_event_name": "PostToolUse",
  "tool_response": {"stdout":"hello-hooks","stderr":"","interrupted":false,
                    "isImage":false,"noOutputExpected":false},
  "duration_ms": 179 }
```

> `duration_ms` 의 설명 원문이 친절합니다. [관찰]
> *"Tool execution time in milliseconds. **Excludes permission-prompt and hook time.**"*
> 순수 툴 실행 시간이지, 여러분이 승인 버튼 누르느라 걸린 시간은 안 들어갑니다.

이벤트별 고유 필드 몇 개입니다. [관찰]

- `UserPromptSubmit` → `prompt`
- `SessionStart` → `source`
- `SessionEnd` → `reason`
- `Stop` → `stop_hook_active`, `last_assistant_message`, `background_tasks`, `session_crons`
- `PostToolBatch` → `tool_calls` 배열 (배치 전체를 한 번에)
- `InstructionsLoaded` → `file_path`, `memory_type`, `load_reason`

> **주의:** 인터넷에서 흔히 보는 `{"inputs": …, "response": …}` 형태는 **옛 표현**입니다. 실제 stdin 은 위처럼 `tool_input` / `tool_response` 입니다. [관찰]

### 페이로드를 직접 보는 가장 쉬운 방법

추측하지 말고 그냥 덤프하세요. 이 조사에서도 이 방법을 썼습니다.

```bash
#!/bin/bash
cat > /tmp/hook-payload-$(date +%s%N).json
exit 0
```

## 계약 (2) — 돌려주는 것

두 가지 방법이 있습니다. **exit code** 와 **JSON 출력**입니다.

### exit code

**`0` / `2` / 그 외** 셋으로 갈립니다. 그리고 **`2` 가 특별합니다.**

| 이벤트 | exit 0 | **exit 2** | 그 외 |
|---|---|---|---|
| `PreToolUse` | 표시 안 함 | **stderr 를 모델에 보이고 툴 호출 차단** | 사용자에게만, 툴은 진행 |
| `PostToolUse` | transcript 에 stdout | stderr 를 모델에 즉시 표시 | 사용자에게만 |
| `UserPromptSubmit` | **stdout 이 모델에게 전달** | **처리 차단 + 원본 프롬프트 삭제** | 사용자에게만 |
| `SessionStart` | **stdout 이 모델에게 전달** | 사용자에게만 | 사용자에게만 |
| `Stop` | 표시 안 함 | **stderr 를 모델에 보이고 대화 계속** | 사용자에게만 |
| `PreCompact` | stdout 이 압축 지시문에 append | 압축 차단 | 진행 |
| `TeammateIdle` | 표시 안 함 | **idle 방지 (계속 작업)** | 사용자에게만 |
| `PostToolBatch` | — | **에이전트 루프 중단** | 사용자에게만 |

> **`Stop` 의 exit 2 를 보세요.** 모델이 "다 했습니다"라고 턴을 끝내려는데, 훅이 **"아니, 아직"** 이라고 막을 수 있습니다. 4편의 의사코드에서 `stop_hook_blocking` 분기가 이것입니다. 그리고 무한루프를 막으려고 연속 차단은 **8 회**로 제한됩니다.

`WorktreeCreate` 만 예외적으로 **0 이 아닌 모든 exit code 가 차단**입니다. [문서]

### JSON 출력

더 정밀하게 제어하려면 stdout 으로 JSON 을 뱉습니다. [관찰]

```json
{
  "systemMessage": "사용자 UI 에 표시할 경고",
  "continue": false,
  "stopReason": "차단할 때 보여줄 메시지",
  "suppressOutput": false,
  "decision": "block",
  "reason": "결정 이유",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "모델 컨텍스트에 주입할 내용"
  }
}
```

핵심 필드입니다.

- **`hookSpecificOutput.additionalContext`** — 모델 컨텍스트에 텍스트를 주입합니다.
- **`hookSpecificOutput.permissionDecision`** — `"allow"` / `"deny"` / `"ask"` (PreToolUse 전용)
- **`hookSpecificOutput.updatedInput`** — **툴 인자를 고쳐서** 실행시킵니다 (PreToolUse 전용)
- `continue: false` — 전체 중단

주의할 점 둘.

1. **`hookSpecificOutput` 에는 반드시 `hookEventName` 을 넣어야 합니다.**
2. **`decision: "block"` 은 PreToolUse 에서 deprecated 입니다.** `permissionDecision` 을 쓰세요.
3. **exit 2 는 JSON 의 `permissionDecision` 으로 덮어쓸 수 없습니다.** [문서] 둘을 섞지 마세요.

## 훅 출력은 대화의 어디로 들어가나

이게 실용적으로 가장 중요한 질문입니다. 실험으로 확인된 경로가 두 개입니다.

### 경로 1 — PreToolUse exit 2 → `tool_result` (is_error)

차단 훅을 만들어봅니다.

```bash
#!/bin/bash
payload=$(cat)
cmd=$(printf '%s' "$payload" | python3 -c "import sys,json;print(json.load(sys.stdin).get('tool_input',{}).get('command',''))")
if [[ "$cmd" == *"FORBIDDEN"* ]]; then
  echo "BLOCKED by policy: command contains FORBIDDEN" >&2
  exit 2
fi
exit 0
```

트랜스크립트에 남은 실제 블록입니다. [관찰]

```json
{"type":"tool_result",
 "content":"PreToolUse:Bash hook error: [/tmp/hooklab2/block.sh]: BLOCKED by policy: command contains FORBIDDEN\n",
 "is_error":true,
 "tool_use_id":"toolu_01WJYt21TjwPai9e8mgYewsJ"}
```

포맷이 정해져 있습니다: **`<이벤트>:<matcher> hook error: [<스크립트 경로>]: <stderr>`**

주목할 점 — **`<system-reminder>` 가 아니라 평범한 `tool_result`** 입니다. 5편에서 본 그 형태 그대로입니다. 그래서 **모델은 이걸 툴 실패로 인식합니다.** 실제로 모델은 차단을 알아차리고 우회를 시도하지 않았습니다. [관찰]

### 경로 2 — UserPromptSubmit additionalContext → `attachment`

이번엔 컨텍스트를 주입해봅니다.

```json
{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit",
  "additionalContext":"MAGIC_TOKEN_12345 the sky is plaid today"}}
```

트랜스크립트에 남은 레코드입니다. [관찰]

```json
{"type":"attachment",
 "attachment":{"type":"hook_additional_context",
               "content":["MAGIC_TOKEN_12345 the sky is plaid today"],
               "hookName":"UserPromptSubmit",
               "hookEvent":"UserPromptSubmit"},
 "uuid":"a75e2682-…","version":"2.1.241"}
```

**2편에서 봤던 `attachment` 레코드입니다.** 그리고 요청을 조립할 때 `<system-reminder>` 로 감싸져 첫 user 메시지에 들어갑니다.

모델은 실제로 이걸 읽었습니다. 응답이 이랬습니다. [관찰]

> *"The magic token in my context is `MAGIC_TOKEN_12345` — it came in via a UserPromptSubmit hook."*

2편에서 `attachment.type` 통계를 냈을 때 `hook_success` 와 `hook_additional_context` 가 압도적으로 많았던 이유가 이겁니다. **제 세션에서 훅이 그만큼 컨텍스트를 채우고 있었던 것**입니다.

## 복붙 예제

바이너리에 내장된 공식 예제 원문입니다. [관찰]

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [{ "type": "command",
                    "command": "jq -r '.tool_input.command' >> ~/.claude/bash-log.txt",
                    "timeout": 5 }] }
    ],
    "PostToolUse": [
      { "matcher": "Write|Edit",
        "hooks": [{ "type": "command",
                    "command": "jq -r '.tool_response.filePath // .tool_input.file_path' | { read -r f; prettier --write \"$f\"; } 2>/dev/null || true" }] }
    ]
  }
}
```

위는 **모든 Bash 명령을 로그로 남기고**, **파일을 쓸 때마다 prettier 를 돌립니다.**

위험한 명령을 막는 훅은 JSON 방식이 권장됩니다.

```bash
#!/bin/bash
cmd=$(jq -r '.tool_input.command // ""')
case "$cmd" in
  *"rm -rf"*)
    jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",
            permissionDecision:"deny",
            permissionDecisionReason:"Destructive command blocked"}}'
    exit 0 ;;
esac
exit 0
```

## 훅이 안 돌 때

```bash
claude --debug hooks
```

디버그 카테고리를 지정할 수 있습니다. `api`, `hooks`, `mcp` 등이고 `!` 로 제외도 됩니다.

체크리스트입니다.

1. **`matcher` 가 그 이벤트에서 뭘 비교하는지** 확인하세요 (위 표).
2. **`timeout` 이 초 단위**인지 확인하세요.
3. **workspace trust 를 수락했는지** 확인하세요. 미수락이면 훅이 아예 안 돕니다. [관찰]
   로그 원문: *"Skipping {event} hook execution - workspace trust not accepted"*
4. **`disableAllHooks` 정책**이 켜져 있는지 확인하세요. [관찰]
   로그 원문: *"Policy disableAllHooks: skipping configured hooks for {event}"*
5. `/hooks` 슬래시 커맨드로 현재 설정을 볼 수 있습니다. 단 **툴 이벤트 위주로만** 보여줍니다.

## 정리

- 훅 이벤트는 **31 개**입니다. 흔히 인용되는 아홉 개는 3분의 1 도 안 됩니다.
- **`matcher` 가 비교하는 필드는 이벤트마다 다릅니다.** 툴 이벤트가 아니면 `tool_name` 이 아닙니다.
- **`timeout` 은 초 단위**입니다.
- stdin 으로 JSON 이 오고, 여기엔 **`transcript_path` 도 들어 있어** 대화 전체를 읽을 수 있습니다.
- **exit 2 가 특별합니다.** PreToolUse 면 툴을 차단하고, Stop 이면 턴을 못 끝내게 막습니다.
- 훅 출력이 들어가는 경로는 두 가지 — 차단은 **`tool_result` (is_error)**, 주입은 **`attachment`** 입니다.
- 훅이 안 돌면 **matcher 필드, timeout 단위, workspace trust** 를 먼저 보세요.

## 확인 못 한 것

1. **`asyncRewake` 훅이 exit 2 로 끝날 때 `<system-reminder>` 로 감싸지는 경로.** 바이너리의 내부 설명 문자열로 존재는 확인했지만, 실제 발화는 재현하지 못했습니다.
2. 31 개 이벤트 중 한 번의 단순 세션에서 실제로 발화한 것은 **10 개**였습니다. 나머지 21 개는 페이로드를 직접 관찰하지 못했습니다.
3. `prompt` / `agent` 타입 훅은 스키마만 확인했고 실행해보지는 않았습니다.

다음 편에서는 **서브에이전트**를 봅니다. 4편에서 "같은 루프 코드"라고 했던 그것 — 왜 쓰는지, 무엇이 오가는지, 그리고 서브에이전트가 12 만 토큰을 쓰고 부모에게 한 줄만 돌려준 실측 사례를.

> 이전 편: [5편. Tool — 모델은 함수를 부르지 않는다](./05-tools.md)
> 다음 편: [7편. 서브에이전트 — 컨텍스트를 지키는 격리](./07-subagents.md)
