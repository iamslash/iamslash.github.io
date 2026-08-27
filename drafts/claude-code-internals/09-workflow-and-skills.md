# 9편. Workflow와 확장 표면 — Skill, 슬래시 커맨드, plan mode

> 시리즈: Claude Code 내부 구조 (builtin 기준, v2.1.243)
> 이 편에서 배우는 것: Skill 의 **점진적 공개(progressive disclosure)** 가 트랜스크립트에 남기는 흔적, plan mode 가 실제로 거는 제약, 그리고 **`Workflow` 툴이 빌트인이라는 것**.

여덟 편에 걸쳐 루프와 그 주변을 봤습니다. 마지막은 **그 위에 얹는 것들**입니다.

## Skill — 설명 한 줄만 먼저 보여준다

### 문제

스킬이 50 개 있다고 합시다. 각 스킬의 지시문이 평균 3,000 자라면 15 만 자입니다. **매 요청마다 이걸 다 보내면** 2편에서 본 컨텍스트 문제가 그대로 터집니다.

### 해법 — 2 단계

**1 단계.** 요청에는 **한 줄짜리 설명만** 들어갑니다. 2편에서 첫 user 메시지를 뜯어봤을 때 봤던 그 블록입니다.

```
[1] <system-reminder> The following skills are available ...   (4,998자)
```

스킬 50 개의 **이름과 한 줄 설명**만 5,000 자 정도로 들어갑니다.

**2 단계.** 모델이 "이 스킬이 필요하다"고 판단하면 `Skill` 툴을 호출하고, **그때 본문이 주입됩니다.**

툴 설명 원문이 이 구조를 그대로 말합니다. [관찰]

> *"Available skills appear in a system-reminder listing with one-line descriptions. When the task at hand is one a listed skill covers, call this tool first — **the skill's instructions load into the turn** for you to follow in place of your default approach."*

### 트랜스크립트로 확인하기

이 조사에서 가장 깔끔한 증거였습니다. `Skill` 툴 호출 전후를 나란히 놓으면 이렇습니다. [관찰]

```
[171632] assistant   tool_use: Skill {"skill":"artifact-design"}
[171633] attachment  hook_success  PreToolUse:Skill
[171634] user        tool_result: "Launching skill: artifact-design"
                     toolUseResult: {"success":true,"commandName":"artifact-design"}
[171635] attachment  hook_success  PostToolUse:Skill
[171637] user  isMeta=True   "Approach this as the design lead at a small studio known for their …"
```

**핵심은 171634 와 171637 의 차이입니다.**

- `tool_result` 는 `"Launching skill: artifact-design"` **한 줄뿐**입니다. 스킬 내용이 아닙니다.
- 실제 스킬 본문은 **그 다음 user 턴**으로 들어옵니다. `isMeta: true` 가 붙어 있습니다.

직접 찾아보려면:

```bash
cd ~/.claude/projects
python3 - <<'PY'
import json,glob,os
for p in sorted(glob.glob('*/*.jsonl'), key=os.path.getmtime, reverse=True):
    try: rows=[json.loads(l) for l in open(p) if l.strip()]
    except Exception: continue
    for i,d in enumerate(rows):
        c=(d.get('message') or {}).get('content')
        if isinstance(c,list) and any(isinstance(b,dict) and b.get('type')=='tool_use'
                                      and b.get('name')=='Skill' for b in c):
            for j in range(i, min(i+9,len(rows))):
                dd=rows[j]; cc=(dd.get('message') or {}).get('content')
                print(j, f"{dd.get('type'):10s}", 'isMeta=', dd.get('isMeta'), '|',
                      json.dumps(dd.get('attachment') or cc, ensure_ascii=False)[:120])
            raise SystemExit
PY
```

제 머신에서 돌린 결과도 같은 모양이었습니다. [관찰]

```
51906 assistant  isMeta= None | [{"type":"tool_use","name":"Skill","input":{"skill":"oh-my-claudecode:canc…
51907 attachment isMeta= None | {"type":"hook_success","hookName":"PreToolUse:Skill", …
51908 attachment isMeta= None | {"type":"hook_additional_context","content":["The boulder never stops. …
51909 user       isMeta= None | [{"type":"tool_result","content":"Launching skill: oh-my-claudecode:…
51910 attachment isMeta= None | {"type":"hook_success","hookName":"PostToolUse:Skill", …
51911 attachment isMeta= None | {"type":"hook_success","hookName":"PostToolUse:Skill", …
51912 user       isMeta= True | [{"type":"text","text":"Base directory for this skill: /Users/iamslash/…
51913 attachment isMeta= None | {"type":"command_permissions","allowedTools":[]}
```

중간에 훅 레코드(6편)가 네 개나 끼어 있는 게 보입니다. 그래서 앞뒤 6 줄만 봐서는 **주입 턴(51912)까지 닿지 않습니다.** 창을 9 줄로 잡은 이유입니다.

> **`isMeta: true` 가 무슨 뜻일까요?** "사람이 친 게 아니라 시스템이 넣은 user 메시지"라는 표시입니다. 1편에서 `promptSource: "system"` 이 1,417 건이었던 것, 7편의 `<task-notification>`, 6편의 훅 주입 — 전부 같은 계열입니다. **대화의 `user` 역할에는 사람 말고도 여러 발신자가 있습니다.**

### `SlashCommand` 툴은 이 빌드에 없다

오래된 글에는 `SlashCommand` 라는 툴이 나옵니다. 2.1.243 에는 없고 **`Skill` 이 그 자리를 대신합니다.**

8편에서 배운 방법론 — 부분문자열과 실제 이름을 구분해서 세기 — 을 씁니다.

```bash
B=$(ls -d ~/.local/share/claude/versions/* | tail -1)
LC_ALL=C strings -n 4 "$B" > /tmp/cc.strings
python3 -c "
d=open('/tmp/cc.strings',encoding='utf-8',errors='replace').read()
print('SlashCommand 부분문자열:', d.count('SlashCommand'))
print('\"SlashCommand\" 리터럴 :', d.count('\"SlashCommand\"'))
print('\"Skill\" 리터럴        :', d.count('\"Skill\"'))"
```

```
SlashCommand 부분문자열: 122
"SlashCommand" 리터럴 : 0      ← 툴 이름으로는 존재하지 않음
"Skill" 리터럴        : 14
```

122 번 나오는 `SlashCommand` 는 전부 `--disable-slash-commands`, `skipSlashCommands` 같은 **플래그 이름**입니다. [관찰]

> **여기서도 방법론이 중요합니다.** `grep SlashCommand` 만 했으면 "122 번 나오니까 있네"라고 결론 낼 뻔했습니다. **툴 이름은 따옴표로 감싸인 리터럴**로 나타난다는 걸 알고 나서야 부재를 확인할 수 있었습니다.

### 스킬 이름 규칙

- 플러그인 스킬: `plugin:skill`
- 디렉터리 스코프 스킬: `apps/web:deploy`
- 둘 다 있으면 **작업 중인 디렉터리를 포함하는 쪽**이 이깁니다 (구체적인 게 우선)

그리고 명시적으로 이렇게 적혀 있습니다. [관찰]

> *"Built-in CLI commands (`/help`, `/clear`, …) aren't skills."*

1편에서 본 그 로컬 실행형 커맨드들 말입니다. **스킬과 슬래시 커맨드는 다른 것**이고, 다만 사용자가 `/name` 으로 스킬을 부를 수는 있습니다.

## 슬래시 커맨드 — 1편의 두 갈래를 마무리

이제 1편의 그림이 완성됩니다.

```
/명령 입력
   │
   ├── 빌트인 local / local-jsx (102개 중 대부분)
   │      → 로컬에서 실행, <local-command-stdout> 기록
   │      → 모델을 부르지 않음                        (1편에서 실측 확인)
   │
   ├── 빌트인 prompt (init, insights, team-onboarding — 3개)
   │      → 프롬프트 텍스트로 확장되어 user 메시지가 됨
   │
   └── 스킬 / 커스텀 커맨드
          → Skill 툴 호출 → 본문이 isMeta:true user 턴으로 주입
```

**"슬래시 커맨드는 텍스트 확장이다"** 라는 흔한 설명은 세 갈래 중 하나에만 맞습니다.

## Plan mode — 툴을 뺏고 프롬프트로 못 박는다

plan mode 는 **툴이 두 개**입니다. [관찰]

```bash
B=$(ls -d ~/.local/share/claude/versions/* | tail -1)
LC_ALL=C grep -ao 'var Iw="EnterPlanMode"' "$B"
LC_ALL=C grep -ao 'var fn="ExitPlanMode"' "$B"
```

진입도 툴로 가능합니다. 예전엔 `Shift+Tab` 전용이었습니다.

### 실제로 거는 제약

시스템 리마인더 원문입니다. [관찰]

> *"**Plan mode is active.** The user indicated that they do not want you to execute yet -- you **MUST NOT** make any edits, run any non-readonly tools (including changing configs or making commits), or otherwise make any changes to the system. **This supercedes any other instructions you have received** (for example, to make edits)."*

**`This supercedes any other instructions you have received`** 라는 문장이 강합니다. `CLAUDE.md` 에 "항상 바로 고쳐라"라고 써놨더라도 plan mode 가 이깁니다.

턴마다 짧게 재확인도 붙습니다. [관찰]

> *"Plan mode still active (see full instructions earlier in conversation). Read-only except plan file (`<path>`)"*

> 8편에서 `Explore`/`Plan` 에이전트가 읽기 전용을 **툴 제한 + 프롬프트**로 이중 방어한다고 했죠. plan mode 도 같은 패턴입니다. 그리고 **매 턴 재확인**까지 붙입니다. 대화가 길어지면 앞쪽 지시가 묻히기 때문입니다.

### 계획은 파일에 쓴다

이게 이전 버전과 크게 다른 점입니다. [관찰]

> *"No plan file exists yet. You should create your plan at `<path>` using the Write tool. You should build your plan incrementally by writing to or editing this file. **NOTE that this is the only file you are allowed to edit** — other than this you are only allowed to take READ-ONLY actions."*

그리고 `ExitPlanMode` 는 **계획 내용을 인자로 받지 않습니다.** [관찰]

> *"This tool does NOT take the plan content as a parameter — **it will read the plan from the file you wrote**. This tool simply signals that you're done planning and ready for the user to review and approve."*

> **왜 이렇게 바꿨을까요?** [추론] 계획을 툴 인자로 넘기면 3편에서 본 `input_json_delta` 로 통째로 스트리밍해야 합니다. 긴 계획이면 느리고, 중간에 끊기면 다 날아갑니다. 파일에 점진적으로 쓰면 부분 진행이 보존되고, 사용자가 승인 전에 직접 편집할 수도 있습니다.

또 하나 명시적 경고가 있습니다. [관찰]

> *"For research tasks where you're gathering information, searching files, reading files or in general trying to understand the codebase - **do NOT use this tool**."*

조사만 하는 작업은 계획 승인 절차를 거칠 필요가 없다는 뜻입니다.

## `Workflow` — 빌트인이다

마지막입니다. 그리고 아마 가장 덜 알려진 것입니다.

**`Workflow` 는 플러그인이 아니라 컴파일된 빌트인 툴입니다.** [관찰]

```bash
B=$(ls -d ~/.local/share/claude/versions/* | tail -1)
LC_ALL=C grep -ao 'var bd="Workflow"' "$B"
LC_ALL=C grep -ao 'aliases:\["RunWorkflow"\]' "$B"
LC_ALL=C grep -ac 'workflow-subagent' "$B"
```

```
var bd="Workflow"
aliases:["RunWorkflow"]
4
```

2편에서 본 툴 목록에도 있었고, **설명이 19,290 자로 전체 툴 중 압도적 1 위**였습니다.

### 무엇을 푸는가

7편에서 서브에이전트를 봤습니다. 그런데 서브에이전트를 **여러 개 조합**하려면 어떻게 할까요?

지금까지의 방식은 **모델이 판단해서 `Agent` 툴을 여러 번 부르는 것**입니다. 유연하지만 문제가 있습니다.

- 모델이 매번 다르게 판단합니다. **재현되지 않습니다.**
- 조건 분기나 반복을 시키면 **모델이 헷갈립니다.** "결과가 0 개면 다시 돌려"를 열 번 반복시키기 어렵습니다.
- 중간 결과를 전부 부모 컨텍스트로 가져와야 판단할 수 있습니다.

`Workflow` 는 **오케스트레이션을 자바스크립트로 적어서 결정적으로 실행**합니다.

### 스크립트 모양

```js
export const meta = {
  name: 'find-flaky-tests',
  description: 'Find flaky tests and propose fixes',
  phases: [
    { title: 'Scan', detail: 'grep test logs for retries' },
    { title: 'Fix',  detail: 'one agent per flaky test' },
  ],
}

phase('Scan')
const flaky = await agent('grep CI logs for retry markers', { schema: FLAKY_SCHEMA })

phase('Fix')
await parallel(flaky.tests.map(t => () =>
  agent(`Fix the flaky test ${t.name}`, { isolation: 'worktree' })
))
```

쓸 수 있는 함수들입니다.

| 함수 | 무엇 |
|---|---|
| `agent(prompt, opts)` | 서브에이전트 하나. `schema` 를 주면 **검증된 객체**로 돌아옴 |
| `parallel(thunks)` | 동시 실행하고 **전부 기다림** (배리어) |
| `pipeline(items, ...stages)` | 항목별로 단계를 통과시킴. **배리어 없음** |
| `phase(title)` | 진행 표시 그룹 |
| `log(msg)` | 사용자에게 진행 상황 표시 |

> `meta` 는 **순수 리터럴**이어야 합니다. 변수나 함수 호출을 쓰면 안 됩니다. [관찰] 실행 전에 정적으로 읽어서 권한 다이얼로그에 보여줘야 하기 때문입니다.

`parallel` 과 `pipeline` 의 차이가 핵심입니다.

```
parallel:  [A1 A2 A3] 전부 끝날 때까지 대기 → [B1 B2 B3]
           ↳ A2 가 느리면 A1·A3 의 B 단계가 놀고 있음

pipeline:  A1 → B1
           A2 ────→ B2
           A3 → B3
           ↳ 각 항목이 독립적으로 진행
```

### 실용적인 것 둘

**1) 스크립트가 디스크에 저장됩니다.** [관찰]

> *"Every Workflow invocation persists its script under the session directory and returns the path in the tool result. To iterate, edit that file with Write/Edit and re-invoke Workflow with the same `scriptPath`."*

**2) 재개하면 캐시가 듣습니다.** [관찰]

> *"Completed `agent()` calls with unchanged (prompt, opts) return their cached results instantly; only edited or new calls re-run."*

즉 20 개 에이전트짜리 워크플로에서 마지막 단계만 고쳤다면, **앞의 19 개는 다시 안 돕니다.** `resumeFromRunId` 로 이어붙입니다.

> 이 캐시 때문에 스크립트에서 **`Date.now()` 와 `Math.random()` 이 금지**됩니다. 매번 값이 달라지면 캐시가 성립하지 않으니까요.

### 동반 인프라

- 전용 에이전트 타입 `workflow-subagent` — 8편에서 봤듯 `Skill`/`Agent`/`Workflow` 툴이 **금지**됩니다. 무한 재귀 방지입니다.
- 슬래시 커맨드 `/workflows`, `/workflow-launch-exec`, `/ultraplan`
- 저장 위치는 두 곳입니다. **미리 정의된** 워크플로는 `.claude/workflows/<name>.js`, 인라인 `script` 로 부른 것은 **세션 디렉터리 안**에 사본이 남습니다 — `~/.claude/projects/<slug>/<session-id>/workflows/scripts/<name>-<runId>.js` [관찰]
- 트랜스크립트 이벤트 타입 `workflow_log`

## 시리즈를 마치며 — 전체 그림

0편에서 이렇게 시작했습니다.

> **LLM API 는 상태가 없다. Claude Code 는 매 턴 전부를 다시 보내는 `while` 루프 하나다.**

아홉 편을 지나 그 주변에 무엇이 붙어 있는지 다 봤습니다.

```
입력 (1편)            첫 글자가 경로를 정한다. @는 툴 호출이 아니다
  ↓
요청 조립 (2편)       system 3블록 · CLAUDE.md는 user 메시지 · 캐시 2+1 · 압축
  ↓
스트리밍 응답 (3편)   SSE · stop_reason 이 루프를 좌우 · 평균 6.8 왕복
  ↓
루프 (4편)            while(true) · 스트리밍 도중 툴 디스패치 · 연속 safe 만 병렬
  ↓
툴 (5편)              JSON 스키마 3키 · 에러도 대화로 · 목록은 고정이 아님 · 권한
  ↓
훅 (6편)              31개 이벤트 · exit 2 가 차단 · tool_result 또는 attachment
  ↓
서브에이전트 (7편)    격리 · 15만 토큰 쓰고 몇 줄만 반환 · untrusted 프레이밍
  ↓
에이전트 종류 (8편)   조건부 목록 · fork 만 예외 · 사라진 에이전트
  ↓
확장 표면 (9편)       Skill 점진적 공개 · plan mode · Workflow 결정적 오케스트레이션
```

### 반복해서 나온 세 가지 패턴

시리즈를 관통한 설계 원칙이 있습니다.

**1) 컨텍스트는 가장 비싼 자원이다.**
프롬프트 캐싱, deferred tools, 스킬의 점진적 공개, 서브에이전트 격리, 자동 압축 — 전부 같은 문제를 다른 각도에서 푼 것입니다.

**2) 방어는 항상 이중이다.**
`Explore` 는 툴을 뺏고 프롬프트로도 못 박습니다. plan mode 는 거기에 매 턴 재확인까지 더합니다. 서브에이전트 결과와 인터럽트 재개 텍스트는 **"데이터지 지시가 아니다"** 라고 명시합니다.

**3) 목록은 고정이 아니다.**
툴도, 에이전트도, 슬래시 커맨드도 조건에 따라 달라집니다. 버전 사이에 사라지기도 합니다.

### 그래서 가장 중요한 것

이 시리즈의 모든 숫자와 목록은 **2.1.243, 제 머신 기준**입니다. 여러분이 읽는 시점엔 이미 다를 수 있습니다.

그래서 결론은 목록이 아니라 **방법**입니다.

```bash
claude --version                                    # 내 버전 확인
ls ~/.claude/projects/                              # 트랜스크립트
jq -r '.body.tools[].name' /tmp/cc-lab/capture/*.json   # 실제 나가는 툴
```

- **트랜스크립트**를 `jq` 로 읽으세요. 이미 쌓여 있습니다.
- **로컬 싱크**로 요청을 캡처하세요. 추측이 필요 없어집니다.
- **부재를 증명할 땐 대조군**을 두세요.
- **바이너리 문자열은 실제 동작이 아닙니다.** 와이어를 보세요.

이 네 가지면 다음 버전에서도 스스로 확인할 수 있습니다.

## 확인 못 한 것

1. **워크플로를 실제로 실행해보지 않았습니다.** 툴 정의와 스키마, 동반 인프라는 바이너리에서 확인했지만 실행 트레이스는 관찰하지 못했습니다.
2. `remote_launched` 상태(클라우드 실행)와 `sessionUrl` 은 재현하지 못했습니다.
3. 스킬의 **백그라운드 실행 변형**은 별도 출력 스키마를 쓴다는 것만 확인했습니다.
4. `/output-style` 슬래시 커맨드는 102 개 목록에서 찾지 못했습니다. 출력 스타일 자체(`Proactive`, `Concise`, `Explanatory`, `Learning`)는 존재하며 진입점은 `/config` 로 보입니다. [추론]

> 이전 편: [8편. 에이전트 종류 — 빌트인 에이전트 목록](./08-agent-types.md)
> 시리즈 처음: [0편. 프롤로그 — Claude Code는 결국 while 루프 하나다](./00-prologue.md)
