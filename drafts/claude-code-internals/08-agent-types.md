# 8편. 에이전트 종류 — 빌트인 에이전트 목록

> 시리즈: Claude Code 내부 구조 (builtin 기준, v2.1.243)
> 이 편에서 배우는 것: 빌트인 에이전트가 **조건에 따라 만들어진다**는 것, 각각이 무엇을 위한 것인지, 내 에이전트를 만드는 법, 그리고 **버전 사이에 에이전트가 사라졌다**는 사실과 그걸 증명하는 방법.

7편에서 `Agent` 툴의 `subagent_type` 필드를 봤습니다. 여기에 무엇을 넣을 수 있을까요?

## 빌트인 목록은 상수가 아니라 함수다

목록을 만드는 코드가 바이너리에 있습니다. **배열 리터럴이 아니라 조건문 덩어리**입니다. [관찰]

```js
function oMe(){
  if (ee.CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS && jt()) return "none";
  if (Pc()) return "coordinator";
  return "default";
}

function aMe(){
  let e = oMe();
  if (e === "none")        return [];
  if (e === "coordinator") return getCoordinatorAgents();

  let t = [SR];                                   // general-purpose
  if (!xm())    t.push(Bgn);                      // statusline-setup
  if (!Jgn())   t.push(CLAUDE_AGENT);             // claude
  if (G6())     t.push(SP, yTe);                  // Explore, Plan
  if (sMe())    t.push(aG);                       // web-fetch agent
  if (ee.CLAUDE_CODE_ENTRYPOINT !== "sdk-ts" &&
      ee.CLAUDE_CODE_ENTRYPOINT !== "sdk-py" &&
      ee.CLAUDE_CODE_ENTRYPOINT !== "sdk-cli") t.push(Ugn);   // claude-code-guide
  return t
}
```

읽어보면 이렇습니다.

- **`general-purpose` 만 무조건** 들어갑니다.
- `Explore` 와 `Plan` 은 게이트 `G6()` 가 켜져야 들어갑니다.
- `claude-code-guide` 는 **SDK 로 실행하면 빠집니다.** CLI 로 쓸 때만 있습니다.
- 환경변수 하나로 **전부 없앨 수도** 있습니다.

> 5편에서 "툴 목록은 고정이 아니다"라고 했죠. **에이전트 목록도 마찬가지입니다.** 이 시리즈가 반복해서 말하는 것 — 목록을 외우지 말고 확인하세요.

## 빌트인 에이전트 여섯 + 내부용 셋

| 이름 | 모델 | 툴 | 무엇을 위한 것 |
|---|---|---|---|
| **`general-purpose`** | 부모 상속 | 전부 (`["*"]`) | 복잡한 조사, 코드 검색, 다단계 작업. "키워드나 파일을 찾는데 몇 번 만에 못 찾을 것 같으면 이걸 써라" |
| **`Explore`** | 상속 (**Opus 로 상한**) | **읽기 전용** | 넓게 훑는 검색. "결론만 필요하고 파일 내용 전체는 필요 없을 때" |
| **`Plan`** | 상속 | **읽기 전용** | 구현 계획 설계. 단계별 계획과 핵심 파일, 아키텍처 트레이드오프를 돌려줌 |
| **`claude`** | 상속 | 전부 | 다른 어디에도 안 맞는 작업의 기본값 |
| **`statusline-setup`** | **Sonnet** | `Read`, `Edit` 만 | 상태줄 설정 |
| **`claude-code-guide`** | **Haiku** | 검색 + 웹 | "Claude Code 가 이거 되나요?" 류 질문 답변 |

내부용도 셋 있습니다. [관찰]

| 이름 | 특징 |
|---|---|
| `fork` | **부모 대화 컨텍스트를 통째로 상속**. 7편의 격리 원칙에서 유일한 예외 |
| `worker` | coordinator 모드 전용. `maxTurns: 200` |
| `workflow-subagent` | 워크플로 스크립트용. `Skill`/`Agent`/`Workflow` 툴이 **금지**됨 (무한 재귀 방지) |

`fork` 가 흥미롭습니다. 7편에서 "자식은 부모 대화를 못 본다"고 했는데, **`fork` 만 예외**입니다. 그래서 `model` 지정도 무시됩니다 — 원문에 *"forks always inherit the parent model"* 이라고 적혀 있습니다. [관찰]

### `Explore` 와 `Plan` 은 읽기 전용을 강하게 못 박는다

두 에이전트의 시스템 프롬프트가 인상적입니다. [관찰]

```
You are a file search specialist for Claude Code…
=== CRITICAL: READ-ONLY MODE - NO FILE MODIFICATIONS ===
This is a READ-ONLY exploration task. You are STRICTLY PROHIBITED from:
- Creating new files (no Write, touch, or file creation of any kind)
- Modifying existing files (no Edit operations)
- Deleting files (no rm or deletion)
- Moving or copying files (no mv or cp)
- Creating temporary files anywhere, including /tmp
- Using redirect operators (>, >>, |) or heredocs to write to files
```

**툴을 뺏는 것으로 끝내지 않고 프롬프트로도 못 박습니다.** `Bash` 가 있는 한 `echo x > file` 로 우회가 가능하니까요. 이중 방어입니다.

> `Explore` 의 설명에 있는 한 문장이 이 에이전트의 성격을 정확히 말해줍니다. [관찰]
> *"It reads excerpts rather than whole files, so it **locates** code; it doesn't **review** or **audit** it."*
> 위치를 찾는 도구지 판단하는 도구가 아닙니다. 리뷰를 시키면 안 됩니다.

## 반전 — 사라진 에이전트

이전 버전 문서나 블로그 글에는 **`output-style-setup`** 이라는 에이전트가 나옵니다. 2.1.243 에는 **없습니다.**

그런데 "grep 했더니 0 이 나왔다"만으로는 증거가 약합니다. **grep 자체가 실패했을 수도** 있으니까요. 그래서 **대조군**을 씁니다.

```bash
B=$(ls -d ~/.local/share/claude/versions/* | tail -1)
for n in general-purpose Explore Plan statusline-setup claude-code-guide \
         output-style-setup web-search-researcher ralph-boulder; do
  printf "%-24s %s\n" "$n" "$(LC_ALL=C grep -ac -- "$n" "$B")"
done
```

```
general-purpose          23
Explore                  42
Plan                    542
statusline-setup          7
claude-code-guide         3
output-style-setup        0   ← 없음
web-search-researcher     0   ← 대조군
ralph-boulder             0   ← 대조군
```

`web-search-researcher` 와 `ralph-boulder` 는 **플러그인에만 존재하는 이름**입니다. 바이너리에 있을 리가 없죠. 이 둘이 0 을 반환하는 걸 확인함으로써 **"이 grep 은 없는 이름에 대해 0 을 돌려준다"** 는 것이 확인됩니다. 그러므로 `output-style-setup` 의 0 은 **진짜 부재**입니다.

> **방법론으로 기억해두세요.** 부재를 증명할 때는 반드시 대조군을 두세요. **"있어야 할 것"과 "없어야 할 것"을 같이 돌려보고**, 후자가 기대대로 0 이 나올 때만 전자의 0 이 의미가 있습니다.

에이전트 타입 문자열을 전수 조사하면 이렇습니다. [관찰]

```bash
python3 -c "
import re,collections
d=open('/tmp/cc.strings',encoding='utf-8',errors='replace').read()
print(collections.Counter(re.findall(r'agentType:\"([a-zA-Z0-9_-]*)\"',d)).most_common())"
```

```
subagent(11) · general-purpose(2) · workflow-subagent(2) · main-session(2) · main(2)
agent(1) · Explore(1) · Plan(1) · statusline-setup(1) · claude(1) · teammate(1)
comment-thread-analyst(1)
```

## 내 에이전트 만들기

마크다운 파일 하나면 됩니다. **frontmatter + 본문**이고, **본문이 곧 시스템 프롬프트**입니다.

### 어디에 두나

우선순위가 높은 순입니다. [문서]

| 위치 | 범위 |
|---|---|
| Managed settings | 조직 전체 |
| `--agents` CLI 플래그 | 현재 세션 |
| `.claude/agents/` | 현재 프로젝트 |
| `~/.claude/agents/` | 모든 프로젝트 |
| 플러그인의 `agents/` | 플러그인 범위 |

이름이 겹치면 **높은 쪽이 이깁니다.**

### 실물 예시

이 시리즈의 조사를 수행한 에이전트가 실제로 이렇게 생겼습니다. [관찰]

```bash
cat ~/.claude/agents/claude-code-internals.md
```

```yaml
---
name: claude-code-internals
description: Explains how the INSTALLED Claude Code actually works by observing it
  directly — the binary, on-disk artifacts, session transcripts, and official docs.
  Every claim comes with a reproducible command. Use for questions like "what did that
  slash command actually do", "how are subagents spawned", …
model: opus
tools: Bash, Read, WebFetch, WebSearch
---

You are Claude Code Internals — an investigator, not a documentation parrot.

Your job: explain how the Claude Code installation ON THIS MACHINE actually
behaves, grounded in evidence you gathered yourself. The user can already read
the docs. What they cannot easily do is watch the machine.
```

**`description` 이 중요합니다.** 부모가 "이 작업을 누구에게 맡길까" 판단하는 근거가 이 문장입니다. 그래서 "무엇을 하는지"보다 **"언제 이걸 써야 하는지"** 를 쓰는 게 좋습니다. 위 예시가 구체적인 질문 예시를 나열한 이유입니다.

### frontmatter 필드

공식 문서에 있는 것들입니다. [문서]

| 필드 | 필수 | 설명 |
|---|---|---|
| `name` | Y | 소문자+하이픈. **훅에서 `agent_type` 으로 노출됨** |
| `description` | Y | 언제 위임할지 |
| `tools` | N | 생략하면 전체 상속 |
| `disallowedTools` | N | 상속 목록에서 제거 |
| `model` | N | `sonnet`/`opus`/`haiku`/`fable` 또는 `inherit`(기본) |
| `permissionMode` | N | 5편의 권한 모드들 |
| `maxTurns` | N | 최대 턴 수 |
| `skills` | N | 시작 시 프리로드할 스킬 |
| `mcpServers` | N | 쓸 MCP 서버 |
| `hooks` | N | 이 에이전트 스코프 훅 |
| `memory` | N | `user`/`project`/`local` |
| `background` | N | true 면 항상 백그라운드 |
| `effort` | N | `low`~`max` |
| `isolation` | N | `worktree` — 격리된 git worktree 에서 실행 |
| `color` | N | UI 색상 |
| `initialPrompt` | N | 메인 에이전트로 뜰 때 자동 제출되는 첫 턴 |

**문서에 없지만 바이너리에 있는 것들**도 찾았습니다. [관찰]

| 필드 | 설명 (원문) |
|---|---|
| `prompt` | "The agent's system prompt" — SDK 용. `.md` 에서는 본문이 이 자리 |
| `observer` | "Agent type auto-spawned as a background observer whenever this agent runs. The observer receives read-only activity digests… it never participates in the task." |
| `observerMessage` | 옵저버에게 보내는 다이제스트에 덧붙일 문구 |
| `observeSubagents` | false 면 자식은 옵저버를 상속하지 않음 |
| `criticalSystemReminder_EXPERIMENTAL` | 시스템 프롬프트에 붙는 실험적 리마인더 |

`observer` 가 흥미롭습니다. **에이전트가 돌 때 감시자를 자동으로 붙이는 기능**입니다. 감시자는 읽기 전용 활동 요약을 받고 작업에는 참여하지 않습니다.

`memory` 를 쓰면 에이전트 전용 메모리 디렉터리가 생깁니다. [관찰]

```
user    → ~/.claude/agent-memory/<agentType>/
project → .claude/agent-memory/<agentType>/
local   → .claude/agent-memory-local/<agentType>/
```

## 조용히 실패하는 함정들

에이전트 로더의 진단 문자열에서 나온 것들입니다. **전부 에러 없이 조용히 실패합니다.** [관찰]

**1) frontmatter 검증에 실패하면 아예 안 뜹니다.**
`name` 은 있는데 `description` 이 없으면 **"never loads"** 입니다. 에러 메시지도 없습니다.

**2) frontmatter 블록이 없으면 이름만 파일명에서 가져옵니다.**
원문: *"At runtime this agent loads with its name taken from the filename and **every other frontmatter field silently dropped**."*

**3) `name` 조차 없으면 그냥 문서로 취급하고 건너뜁니다.**

**4) 같은 디렉터리에서 `name` 이 겹치면 — 머신마다 다른 게 이깁니다.**
원문: *"which definition is live can differ between machines"*
승자가 `readdir` 순서로 정해지고, **그 순서는 정렬되지 않습니다.**

**5) 하위 디렉터리도 스캔합니다.**
`.claude/agents/old/` 에 치워둔 파일도 로드됩니다. 치우려면 디렉터리 밖으로 옮기거나 확장자를 바꾸세요.

> **에이전트가 안 뜬다면 이 순서로 보세요.** ① `description` 이 있는가 → ② frontmatter 구분선 `---` 이 제대로 있는가 → ③ 같은 이름이 다른 데 있는가 → ④ 하위 디렉터리에 옛 버전이 남아 있는가.

지금 로드된 에이전트를 확인하려면:

```bash
ls -la ~/.claude/agents/ ; ls -la ./.claude/agents/ 2>/dev/null
```

## 정리

- **빌트인 에이전트 목록은 조건부로 만들어집니다.** `general-purpose` 만 무조건 있고, 나머지는 게이트·엔트리포인트에 따라 달라집니다.
- 빌트인은 여섯 개(`general-purpose`, `Explore`, `Plan`, `claude`, `statusline-setup`, `claude-code-guide`) + 내부용 셋(`fork`, `worker`, `workflow-subagent`).
- **`Explore`/`Plan` 은 읽기 전용**을 툴 제한과 프롬프트로 이중 방어합니다.
- **`fork` 만 부모 컨텍스트를 상속**합니다. 7편 격리 원칙의 유일한 예외입니다.
- **`output-style-setup` 은 2.1.243 에서 사라졌습니다.** 부재를 증명할 땐 **대조군**을 쓰세요.
- 내 에이전트는 **frontmatter + 본문(=시스템 프롬프트)** 마크다운 하나면 됩니다. `description` 이 위임 판단의 근거입니다.
- 로더는 **조용히 실패합니다.** `description` 누락, 이름 충돌, 하위 디렉터리 잔재를 의심하세요.

## 확인 못 한 것

1. **`G6()`, `sMe()`, `Jgn()` 등 게이트 함수의 판정 조건.** 난독화된 이름이라 어떤 플래그를 읽는지 함수 단위로는 특정하지 못했습니다.

> **뒤늦게 알아낸 것 — 게이트를 직접 열거할 수 있습니다.** [관찰]
> 이 시리즈를 쓰는 내내 "서버 사이드 실험이라 알 수 없다"고 적었는데, **`~/.claude.json` 에 캐시가 통째로 들어 있습니다.**
>
> ```bash
> python3 -c "
> import json,os
> d=json.load(open(os.path.expanduser('~/.claude.json')))
> gb=d.get('cachedGrowthBookFeatures') or {}
> print('키', len(gb), '개')
> print([k for k in sorted(gb) if 'hazel' in k or 'amber' in k][:8])"
> ```
>
> 제 머신에선 **551 개**가 나왔습니다. 그중에는 4편에서 다룬 **서브에이전트 중첩 깊이(기본 3)를 제어하는** 플래그 `tengu_hazel_trellis` 도 있었습니다.
> 단, 캐시는 **플래그 이름과 값의 목록**일 뿐입니다. 이 게이트 함수가 **어느 플래그를 읽는지**까지 알려주진 않습니다.
> 캐시에 **없는** 이름은 기본값으로 동작한다는 뜻이라, 없는 것도 정보입니다.

2. `coordinator` 모드에서 나오는 에이전트 목록(`getCoordinatorAgents()`)은 활성화해보지 못했습니다.
3. `observer` / `observerMessage` / `observeSubagents` 는 문자열로만 확인했고 실제로 동작시켜보지 못했습니다.
4. `isolation: worktree` 의 실제 동작도 재현하지 않았습니다.

다음 편은 마지막입니다. **Workflow** 툴 — 빌트인에 실제로 들어 있는 오케스트레이션 도구 — 과 확장 표면(Skill, 슬래시 커맨드, plan mode)을 봅니다.

> 이전 편: [7편. 서브에이전트 — 컨텍스트를 지키는 격리](./07-subagents.md)
> 다음 편: [9편. Workflow와 확장 표면 — Skill, 슬래시 커맨드, plan mode](./09-workflow-and-skills.md)
