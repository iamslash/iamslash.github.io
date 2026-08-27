# 2편. 요청 바디 해부 — LLM에게 실제로 보내는 것

> 시리즈: Claude Code 내부 구조 (builtin 기준, v2.1.243)
> 이 편에서 배우는 것: 시스템 프롬프트가 정확히 몇 조각인지, `CLAUDE.md` 가 어디에 들어가는지(대부분 틀리게 알고 있습니다), 프롬프트 캐시가 어떻게 붙는지, 그리고 대화가 길어지면 무슨 일이 벌어지는지.

1편에서 여러분의 입력이 메시지 배열이 되는 과정을 봤습니다. 이제 그 배열이 **HTTP 요청으로 조립되는 순간**을 봅니다.

0편에서 세팅한 로컬 싱크로 캡처한 요청의 최상위 키는 아홉 개였습니다. [관찰]

```bash
jq '.body | keys' /tmp/cc-lab/capture/req02.json
```

```json
["context_management","max_tokens","messages","metadata","model","stream","system","thinking","tools"]
```

이번 편은 이 중 셋 — `system`, `messages`, `tools` — 을 뜯어봅니다. 나머지는 값이 단순합니다. [관찰]

```
model      = claude-haiku-4-5-20251001
max_tokens = 32000
stream     = true
thinking   = {"budget_tokens":31999,"type":"enabled","display":"omitted"}
```

## HTTP 봉투부터

```
POST https://api.anthropic.com/v1/messages?beta=true
```

캡처된 실제 헤더 일부입니다. [관찰]

```
User-Agent: claude-cli/2.1.243 (external, sdk-cli)
anthropic-version: 2023-06-01
anthropic-beta: interleaved-thinking-2025-05-14, thinking-token-count-2026-05-13,
                context-management-2025-06-27, prompt-caching-scope-2026-01-05,
                claude-code-20250219, advisor-tool-2026-03-01
X-Stainless-Package-Version: 0.112.1
X-Stainless-Timeout: 600
```

두 가지가 눈에 띕니다.

**첫째, `X-Stainless-*` 헤더**는 공식 TypeScript SDK(`@anthropic-ai/sdk`)가 붙이는 것입니다. Claude Code 는 특별한 내부 프로토콜을 쓰는 게 아니라 **여러분이 `npm install` 할 수 있는 그 SDK 를 씁니다.**

**둘째, `anthropic-beta` 목록**이 Claude Code 가 쓰는 기능을 그대로 드러냅니다. `interleaved-thinking`, `prompt-caching-scope`, `context-management` — 이번 편에서 볼 것들입니다.

## `system` 은 문자열이 아니라 배열이다 — 정확히 3블록

시스템 프롬프트를 긴 문자열 하나로 생각하기 쉽지만, 실제로는 **블록 3개짜리 배열**입니다. [관찰]

| # | 내용 | `cache_control` | 크기 |
|---|---|---|---|
| 0 | `x-anthropic-billing-header: cc_version=…` | **없음** | 74자 |
| 1 | 정체성 한 줄 | `{"type":"ephemeral"}` | 62자 |
| 2 | 본문 전체 (규범 + Environment + gitStatus) | `{"type":"ephemeral"}` | **27,824자** |

```bash
jq -r '.body.system[] | "\(.text|length)\t\(.cache_control)"' /tmp/cc-lab/capture/req02.json
```

블록 1, 즉 "정체성 한 줄"은 **실행 방식에 따라 세 가지 중 하나**가 선택됩니다. 번들의 실제 코드입니다. [관찰]

```js
Wnt = "You are Claude Code, Anthropic's official CLI for Claude."
jtn = "You are Claude Code, Anthropic's official CLI for Claude, running within the Claude Agent SDK."
Htn = "You are a Claude agent, built on Anthropic's Claude Agent SDK."

if (e?.isNonInteractive) { if (e.hasAppendSystemPrompt) return jtn; return Htn }
return Wnt
```

즉 터미널에서 대화형으로 쓰면 `Wnt`, `claude -p` 로 한 번만 실행하면 `Htn` 입니다. **같은 프로그램인데 자기 소개가 달라집니다.**

```bash
B=$(ls -d ~/.local/share/claude/versions/* | tail -1)
LC_ALL=C strings -n 4 "$B" | grep -o "You are Claude Code, Anthropic's official CLI for Claude[^\\\\]*" | sort -u
```

## 반전 — `CLAUDE.md` 는 시스템 프롬프트에 없다

여기가 이 편의 핵심입니다.

`CLAUDE.md` 에 프로젝트 규칙을 적으면 "시스템 프롬프트에 들어간다"고 흔히 설명합니다. **아닙니다.** 캡처해보면 `CLAUDE.md` 내용은 시스템 프롬프트 어디에도 없고, **첫 user 메시지 안의 `<system-reminder>` 블록**에 들어 있습니다. [관찰]

```
<system-reminder>
As you answer the user's questions, you can use the following context:
# claudeMd
Codebase and user instructions are shown below. Be sure to adhere to these instructions.
IMPORTANT: These instructions OVERRIDE any default behavior and you MUST follow them exactly as written.

Contents of <CONFIG_DIR>/CLAUDE.md (user's private global instructions for all projects):
...
# currentDate
Today's date is 2026-08-24.

      IMPORTANT: this context may or may not be relevant to your tasks. ...
</system-reminder>
```

마지막 문장을 보세요. **"this context may or may not be relevant"** — "관련 없을 수도 있다"고 덧붙이고 있습니다. 시스템 프롬프트의 절대적 지시와는 톤이 다릅니다.

### 병합 순서

`CLAUDE.md` 는 여러 곳에 있을 수 있습니다. 네 개를 전부 만들어 놓고 캡처하면 이 순서로 이어붙습니다. [관찰]

1. `$CLAUDE_CONFIG_DIR/CLAUDE.md` — 사용자 전역
2. `<cwd>/CLAUDE.md` — 프로젝트
3. `<cwd>/.claude/CLAUDE.md` — 프로젝트
4. `<cwd>/CLAUDE.local.md` — 개인용(커밋 안 함)

```bash
S=/tmp/cc-lab
printf '# USER GLOBAL\n' > $S/cfg/CLAUDE.md
printf '# PROJECT\n'     > $S/lab/CLAUDE.md
mkdir -p $S/lab/.claude && printf '# DOT-CLAUDE\n' > $S/lab/.claude/CLAUDE.md
printf '# LOCAL\n'       > $S/lab/CLAUDE.local.md
CLAUDE_CONFIG_DIR=$S/cfg ANTHROPIC_BASE_URL=http://127.0.0.1:8931 \
  ANTHROPIC_API_KEY=sk-ant-fake claude -p "memory order test" --model claude-haiku-4-5-20251001
jq -r '.body.messages[].content[]?.text // empty' $S/capture/req0*.json | grep -A40 '# claudeMd'
```

### 하위 디렉터리의 CLAUDE.md 는 처음엔 안 들어간다

`apps/backend/CLAUDE.md` 같은 하위 디렉터리 메모리는 **첫 요청에 포함되지 않습니다.** 그 디렉터리의 파일을 실제로 읽을 때 비로소 주입됩니다. [관찰]

```bash
cd ~/.claude/projects
grep -o 'nested_memory' ./*/*.jsonl | wc -l
```

> 대규모 모노레포에서 모든 하위 `CLAUDE.md` 를 처음부터 밀어넣지 않으려는 설계입니다. 대신 **"왜 내 규칙을 안 지키지?"** 의 흔한 원인이기도 합니다 — 그 디렉터리 파일을 아직 안 읽었으면 모델은 그 규칙을 본 적이 없습니다.

## 반대로 — `gitStatus` 는 시스템 프롬프트에 있다

재미있게도 방향이 반대인 것도 있습니다. 시스템 프롬프트 블록 2의 꼬리를 보면 [관찰]:

```
# Environment
You have been invoked in the following environment:
 - Primary working directory: /tmp/cc-lab/lab
 - Is a git repository: true
 - Platform: darwin
 - You are powered by the model named Haiku 4.5. ...

gitStatus: This is the git status at the start of the conversation.
Current branch: main
Status:
M note.txt
Recent commits:
70e9e04 init
```

**브랜치 이름과 커밋 로그가 시스템 프롬프트 안에 있습니다.**

이게 왜 중요할까요? **프롬프트 캐시가 갈리기 때문**입니다. 블록 2 에는 `cache_control` 이 붙어 있는데, 브랜치를 바꾸거나 커밋을 하나 하면 이 블록의 내용이 달라지고 **캐시가 통째로 무효화**됩니다.

플래그 하나로 이 배치를 바꿀 수 있습니다. [관찰]

```bash
claude -p "x" --exclude-dynamic-system-prompt-sections
# system[2]: 27,824자 → 26,725자 (Environment/gitStatus 빠짐)
# 대신 첫 user 메시지의 <system-reminder> 로 이동
```

> **정리하면 이렇습니다.**
> `CLAUDE.md` → user 메시지 · `gitStatus` → system 프롬프트.
> 직관과 반대입니다. 그래서 캐시 동작을 예측하려면 실제 캡처를 봐야 합니다.

## 첫 user 메시지의 속사정

첫 user 메시지는 여러분이 친 텍스트 하나가 아닙니다. **블록 여러 개**입니다. [관찰]

```
[0] <system-reminder> 사용 가능한 에이전트 타입 목록          (1,786자)
[1] <system-reminder> 사용 가능한 스킬 목록                   (4,998자)
[2] <system-reminder> UserPromptSubmit 훅 출력               (훅이 있을 때만)
[3] <system-reminder> CLAUDE.md + 오늘 날짜                   (746자)
[4] 여러분이 실제로 친 텍스트                       ← cache_control: ephemeral
```

여러분의 프롬프트는 **맨 마지막 블록 하나**입니다. 앞의 7,500 자는 전부 하네스가 붙인 것입니다.

훅이 정말 여기 들어가는지 직접 확인해봅시다. [관찰]

```bash
S=/tmp/cc-lab
cat > $S/cfg/settings.json <<'EOF'
{"hooks":{"UserPromptSubmit":[{"hooks":[{"type":"command","command":"printf 'HOOK_SAW_PROMPT_12345'"}]}]}}
EOF
CLAUDE_CONFIG_DIR=$S/cfg ANTHROPIC_BASE_URL=http://127.0.0.1:8931 \
  ANTHROPIC_API_KEY=sk-ant-fake claude -p "hello hook" --model claude-haiku-4-5-20251001
jq -r '.body.messages[].content[]?.text // empty' $S/capture/req0*.json | grep HOOK_SAW
```

```
<system-reminder>
UserPromptSubmit hook success: HOOK_SAW_PROMPT_12345
</system-reminder>
```

**셸 스크립트의 표준출력이 모델의 컨텍스트에 그대로 들어갔습니다.** 6편의 주제입니다.

### `attachment` 의 정체

1편에서 트랜스크립트에 `attachment` 레코드가 제일 많았던 걸 기억하시나요? 이제 연결됩니다. **트랜스크립트에는 원본과 부가 컨텍스트가 따로 저장되고, `<system-reminder>` 로 감싸는 일은 요청을 조립하는 시점에 일어납니다.** [관찰]

```bash
cd ~/.claude/projects && python3 -c "
import json,glob,collections
c=collections.Counter()
for f in glob.glob('*/*.jsonl'):
    for l in open(f):
        if '\"attachment\"' not in l: continue
        try: o=json.loads(l)
        except: continue
        if o.get('type')=='attachment': c[o['attachment'].get('type')]+=1
[print(v,k) for k,v in c.most_common(12)]"
```

제 머신 결과입니다. [관찰]

```
163122 hook_success
 61099 hook_additional_context
  6732 task_reminder
  2749 total_tokens_reminder
  2210 queued_command
   813 edited_text_file
   362 file
   281 date_change
   225 deferred_tools_delta
   211 compact_file_reference
   180 agent_listing_delta
    98 todo_reminder
```

> **주의:** 이 숫자는 제 머신 기준이고, 저는 훅을 많이 걸어둔 상태라 `hook_success` 가 비정상적으로 큽니다. 순수 builtin 이라면 훨씬 작습니다. **종류**를 보시면 됩니다.

`edited_text_file` 이 흥미롭습니다. 여러분이 에디터에서 파일을 고치면 그 사실이 대화에 주입됩니다. `date_change` 는 자정을 넘기면 날짜를 갱신해줍니다.

## `tools` 배열 — 그리고 없는 것들

기본 `-p` 세션에서 28 개가 전송됐습니다. [관찰]

```bash
jq -r '.body.tools[] | "\(.name)\t\(.description|length)"' /tmp/cc-lab/capture/req02.json
```

```
Agent Bash CronCreate CronDelete CronList DesignSync Edit EnterWorktree ExitWorktree
ListAgents Monitor NotebookEdit PushNotification Read ReportFindings ScheduleWakeup
SendMessage Skill TaskCreate TaskGet TaskList TaskOutput TaskStop TaskUpdate
WebFetch WebSearch Workflow Write
```

각 툴 객체는 `{name, description, input_schema}` 세 키뿐이고 **`cache_control` 이 붙지 않습니다.**

여기서 이상한 점을 눈치채셨나요? **`Grep` 과 `Glob` 이 없습니다.** `TodoWrite` 도 없습니다.

이들은 **deferred tools** 로 분리되어, 모델이 `ToolSearch` 로 필요할 때 스키마를 불러오는 구조입니다. [관찰]

```bash
cd ~/.claude/projects && grep -o 'deferred_tools_delta' ./*/*.jsonl | wc -l
```

> **왜 이렇게 할까요?** 툴 정의는 공짜가 아닙니다. `Workflow` 하나의 설명만 **19,290 자**입니다. 툴 100 개를 매 요청마다 다 보내면 컨텍스트가 툴 설명으로 가득 찹니다. 그래서 자주 쓰는 것만 미리 보내고 나머지는 필요할 때 꺼내옵니다. 5편에서 이어집니다.

## 프롬프트 캐싱 — 고정 2개 + 롤링 1개

0편에서 "매 요청마다 전부 다시 보낸다"고 했습니다. 그럼 같은 앞부분을 계속 재전송하게 되는데, 이걸 그냥 두면 낭비입니다. `cache_control` 이 그 해법입니다.

**턴 1** — 요청에 메시지 1개일 때 [관찰]

```
system[0]  cache_control = null
system[1]  cache_control = ephemeral      ★ 고정
system[2]  cache_control = ephemeral      ★ 고정
messages[0].content[0]  null    ← 에이전트 목록
messages[0].content[1]  null    ← 스킬 목록
messages[0].content[2]  null    ← claudeMd
messages[0].content[3]  ephemeral         ★ 롤링
```

**턴 2** — 툴을 한 번 쓰고 난 뒤 [관찰]

```
system[1]  ephemeral      ★ 고정 (그대로)
system[2]  ephemeral      ★ 고정 (그대로)
messages[0].*   null      ← 아까의 롤링 마커가 사라짐
messages[1].*   null      ← assistant 응답
messages[2].content[0]  ephemeral   ★ 롤링 마커가 tool_result 로 이동
```

즉 **고정 2개(system) + 롤링 1개(항상 마지막 블록)** 구조입니다. 롤링 마커는 매 턴 대화의 끝을 따라 이동하면서 "여기까지는 캐시해둬"라고 표시합니다.

### 캐시가 실제로 히트하는 걸 눈으로 보기

트랜스크립트의 `usage` 필드로 확인할 수 있습니다.

```bash
cd ~/.claude/projects
f=$(ls -t ./*/*.jsonl | head -1)
jq -r 'select(.type=="assistant") | [.requestId, .message.stop_reason,
  .message.usage.input_tokens, .message.usage.cache_creation_input_tokens,
  .message.usage.cache_read_input_tokens, .message.usage.output_tokens] | @tsv' "$f" \
  | awk '!seen[$1]++' | head -7
```

> **함정 하나.** `~/.claude/projects` 아래에는 디렉터리 이름이 `-` 로 시작하는 것들이 있습니다(경로의 `/` 를 `-` 로 바꾼 이름이라 그렇습니다). `ls -t */*.jsonl` 로 쓰면 `ls` 가 그걸 **옵션으로 오해**합니다. 그래서 `./*/*.jsonl` 로 씁니다.

제 세션의 실제 출력입니다. [관찰]

```
req_011CeNVQwP8A5fw4B5WUu16C  tool_use   2  53641      0  4470
req_011CeNVVLBS8ncA4kxmG6rGG  tool_use   2   5398  53641   436
req_011CeNVVh72KGpiZmr4bMiVG  tool_use   2   2424  59039   344
req_011CeNVW1kSeiBi4gfWnnCU1  tool_use   2   4628  61463   525
req_011CeNVWbTUpbFA27BXpwCNR  tool_use   2    848  66091   861
req_011CeNVXXyQL2YiLBLjdfPkG  tool_use   2   1097  66939   256
req_011CeNVXqSPAudokEfARTyVx  end_turn   2    345  68036   135
```

읽는 법:

- **3번째 열 `input_tokens` 가 계속 `2`** 입니다. 캐시되지 않은 새 입력이 사실상 없다는 뜻입니다.
- **5번째 열 `cache_read` 가 0 → 53,641 → … → 68,036** 으로 단조 증가합니다. 매 턴 이전 전체를 캐시에서 읽어옵니다.
- **4번째 열 `cache_creation`** 은 이번 턴에 새로 캐시에 쓴 양입니다.
- 마지막 줄만 `stop_reason` 이 `end_turn` 입니다. 나머지는 전부 `tool_use` — **루프가 여섯 번 돌았다**는 뜻입니다. 3편의 주제입니다.

> `awk '!seen[$1]++'` 를 왜 붙였을까요? 빼고 돌려보면 **같은 `requestId` 가 여러 줄 반복**됩니다. 응답 하나가 트랜스크립트에는 여러 줄로 쪼개져 저장되기 때문입니다. 4편에서 다룹니다.

## 대화가 너무 길어지면 — 자동 압축

컨텍스트 윈도우는 유한합니다. 한계에 가까워지면 Claude Code 는 **지금까지의 대화를 요약해서 갈아끼웁니다.**

번들의 실제 임계값 계산식입니다. [관찰]

```js
var BGn = 13000, jGn = 3000, mBe = 0.2;

function hBe(e /*window*/, t){
  let n = e - 13000;        // 요약을 쓸 자리 13,000 토큰을 남겨둔다
  ...
  return n;
}
function Ykt(e /*used*/, t /*window*/, ...){
  let s = hBe(t, n);        // 압축 임계
  let a = s - 20000;        // 경고 임계
  let c = r - 3000;         // 차단 임계
  if (e >= c) return {level:"blocked"};
  if (e >= s) return {level:"compact"};
  if (e >= a) return {level:"warn"};
  return {level:"ok"};
}
```

여기서 흔히 빠뜨리는 게 하나 있습니다. `Ykt` 에 넘어가는 "윈도우"는 **원본 윈도우가 아닙니다.** 호출부를 보면 `VGn()` 을 거치는데, 이 함수가 **출력용으로 최대 20,000 토큰을 미리 떼어놓습니다.** [관찰]

```js
var QGn = 20000;
function xD(e,t){ let n = Math.min(nK(e), QGn); let {window:o} = PD(e,r); return o - n }
//                    ↑ 출력 예약분을 뺀 "유효 윈도우"
```

그래서 실효 계산은 이렇게 됩니다.

```
유효 윈도우 = 원본 윈도우 − min(max_tokens, 20,000)
압축 = 유효 윈도우 − 13,000
경고 = 압축 − 20,000
차단 = 유효 윈도우 − 3,000
```

| 윈도우 | 경고 | 압축 | 차단 |
|---|---|---|---|
| 200K | 147,000 | 167,000 | 177,000 |
| 1M | 947,000 | **967,000** | 977,000 |

1M 행의 `967,000` 은 계산만 맞는 게 아니라 **바이너리에 리터럴로 박혀 있습니다.** [관찰]

```bash
B=~/.local/share/claude/versions/2.1.243
LC_ALL=C strings -n 4 "$B" | grep -o 'default:967000' | head -1
```

압축이 일어나면 트랜스크립트에 경계 레코드가 남습니다. [관찰]

```json
{"type":"system", "subtype":"compact_boundary", "content":"Conversation compacted",
 "compactMetadata":{
   "trigger":"manual",
   "preTokens":765714,
   "postTokens":12384,
   "durationMs":131978, ...}}
```

**765,714 토큰이 12,384 토큰이 됐습니다.** 62분의 1 입니다.

내 세션들의 압축 이력을 전부 뽑아봅시다.

```bash
cd ~/.claude/projects && python3 - <<'PY'
import json,glob,collections
rows=[]; trig=collections.Counter()
for p in glob.glob('*/*.jsonl'):
    try:
        for l in open(p):
            if 'compact_boundary' not in l: continue
            d=json.loads(l)
            if d.get('subtype')!='compact_boundary': continue
            m=d.get('compactMetadata') or {}
            if not m: continue
            trig[m.get('trigger')]+=1
            rows.append((m.get('trigger'),m.get('preTokens'),m.get('postTokens'),m.get('durationMs')))
    except Exception: pass
print("총",len(rows),"건 :",dict(trig))
for r in rows[:5]: print(r)
PY
```

제 머신 결과입니다. [관찰]

```
총 115 건 : {'manual': 110, 'auto': 5}
('auto',   1001175, 15586, 148812)
('auto',   1001950, 17226, 157788)
('auto',   1006921, 24989, 196782)
('manual',  765714, 12384, 131978)
('manual',  884788, 14743, 163068)
```

`trigger` 가 `auto` 인 것이 **자동 압축**, `manual` 이 `/compact` 를 직접 친 것입니다. 압축의 대부분(110/115)이 수동이라는 게 눈에 띕니다 — 자동으로 터지기 전에 미리 정리한 경우입니다.

> **압축은 공짜가 아닙니다.** 위에서 `durationMs` 가 131,978 — **2분 12초**입니다. 요약을 만들려고 LLM 을 또 부르기 때문입니다. 그리고 요약은 손실 압축입니다. 그래서 중요한 제약은 `CLAUDE.md` 에 적어두는 게 안전합니다 — 그건 매 요청마다 다시 주입되니까요.

## 정리

- `system` 은 문자열이 아니라 **블록 3개짜리 배열**입니다. 정체성 한 줄조차 실행 방식에 따라 달라집니다.
- **`CLAUDE.md` 는 시스템 프롬프트에 없습니다.** 첫 user 메시지의 `<system-reminder>` 안에 들어갑니다.
- **반대로 `gitStatus` 와 `# Environment` 는 시스템 프롬프트에 있습니다.** 그래서 브랜치를 바꾸면 캐시가 깨집니다.
- 첫 user 메시지에서 **여러분이 친 텍스트는 마지막 블록 하나**뿐입니다.
- 툴 28 개가 전송되고, **`Grep`/`Glob` 은 그 안에 없습니다** — 필요할 때 꺼내오는 deferred tool 입니다.
- 캐시 브레이크포인트는 **고정 2개 + 롤링 1개**. `cache_read` 가 단조 증가하면 잘 맞고 있는 것입니다.
- 컨텍스트가 차면 **요약으로 갈아끼웁니다.** 76만 토큰 → 1.2만 토큰, 대신 2분 12초.

## 확인 못 한 것

1. ~~자동 압축의 실제 발화 임계값~~ → **해결됐습니다.** 관찰된 `preTokens`(1,001,175 / 1,001,950 / 1,006,921)가 위 표의 967,000 을 훌쩍 넘긴 이유는, **1M 컨텍스트 베타에서는 선제적 자동 압축 경로 자체가 건너뛰어지기 때문**입니다. 윈도우가 정확히 1,000,000 이라는 것도 API 에러 문구로 확인됐습니다 — `prompt is too long: 1252025 tokens > 1000000 maximum`. 즉 그 경우엔 **API 가 거부할 때까지 밀어붙이는 반응형 경로만** 남고, `preTokens` 는 100 만을 넘긴 뒤 측정됩니다. (자세한 분기 조건은 시즌 2 에서 다룹니다.)
2. `metadata.user_id` 에 담기는 값의 정확한 구성. `device_id` 해시와 세션 ID 가 보이는 것까지만 확인했습니다.

다음 편에서는 이 요청에 대한 **응답**을 봅니다. 스트리밍은 어떤 순서로 오는지, 그리고 위 표에서 계속 보였던 `stop_reason` 이 왜 루프 전체를 좌우하는지.

> 이전 편: [1편. 엔터를 치면 무슨 일이 일어나는가](./01-prompt-to-messages.md)
> 다음 편: [3편. 응답 — SSE 스트리밍과 stop_reason](./03-streaming-and-stop-reason.md)
