# 3편. Workflow ① — 결정적 오케스트레이션의 계약

> 시리즈: Claude Code 멀티에이전트 (builtin 기준)
> 이 편에서 배우는 것: `Workflow` 가 **빌트인**이라는 것, 모델이 정하는 조율과 코드가 정하는 조율의 차이, 스크립트 형식, 그리고 실행이 디스크에 남기는 것.

지금까지 두 편은 **모델이 판단해서** 자식을 부르는 방식이었습니다. 부모가 "이건 나눠서 하는 게 낫겠다"고 판단하고 `Agent` 툴을 호출하죠.

유연합니다. 그런데 한계가 있습니다.

## 모델이 조율할 때의 문제

파일 서른 개를 각각 검토하고 싶다고 해봅시다. 모델에게 맡기면:

- **재현되지 않습니다.** 같은 요청을 두 번 해도 몇 개를 병렬로 띄울지, 어떤 순서로 갈지 매번 다릅니다.
- **반복과 조건을 시키기 어렵습니다.** "결과가 0 개면 다시 돌려"를 열 번 반복시켜 보세요. 모델이 중간에 지치거나 헷갈립니다.
- **중간 결과를 부모가 다 봐야 합니다.** 판단하려면 봐야 하고, 보면 0편에서 본 컨텍스트 문제가 그대로 돌아옵니다.

세 번째가 특히 아픕니다. **컨텍스트를 아끼려고 나눴는데, 조율하려고 다시 모으는** 셈이니까요.

`Workflow` 는 **오케스트레이션을 자바스크립트로 적어서 결정적으로 실행**합니다.

## 먼저 — 이건 빌트인입니다

플러그인이나 서드파티 도구로 오해하기 쉽습니다. 아닙니다. 시즌 1 의 9편에서 배운 **따옴표 리터럴** 기법으로 확인합니다.

```bash
B=~/.local/share/claude/versions/2.1.243
LC_ALL=C strings -n 4 "$B" > /tmp/s243.txt
python3 -c "
d=open('/tmp/s243.txt',encoding='utf-8',errors='replace').read()
for n in ['Workflow','RunWorkflow','workflow-subagent','workflow_log','ZZQuuxNotAThing']:
    print(f'{n:20s} 부분문자열={d.count(n):4d}  따옴표리터럴={d.count(chr(34)+n+chr(34)):3d}')"
```

```
Workflow             부분문자열= 677  따옴표리터럴=  4
RunWorkflow          부분문자열=   3  따옴표리터럴=  1
workflow-subagent    부분문자열=   4  따옴표리터럴=  2
workflow_log         부분문자열=  54  따옴표리터럴= 39
ZZQuuxNotAThing      부분문자열=   0  따옴표리터럴=  0
```

대조군이 0 이므로 나머지는 의미가 있습니다. [관찰] 번들에 이렇게 박혀 있습니다.

```js
var bd = "Workflow";
sn({ name: bd, aliases: ["RunWorkflow"], maxResultSizeChars: 1e5, ... })
```

동반 인프라도 있습니다 — 전용 에이전트 타입 `workflow-subagent`, 트랜스크립트 이벤트 `workflow_log`, 슬래시 커맨드 `/workflows`.

> **시즌 1 의 2편을 기억하시나요?** 툴 목록에서 `Workflow` 의 설명이 **19,290 자**로 유난히 컸습니다. 툴 하나에 매뉴얼 한 권이 붙어 있는 셈입니다.

## 스크립트의 모양

```js
export const meta = {
  name: 'find-flaky-tests',
  description: 'Find flaky tests and propose fixes',
  phases: [
    { title: 'Scan', detail: 'grep CI logs for retries' },
    { title: 'Fix',  detail: 'one agent per flaky test' },
  ],
}

phase('Scan')
const flaky = await agent('grep CI logs for retry markers', { schema: FLAKY_SCHEMA })

phase('Fix')
await parallel(flaky.tests.map(t => () =>
  agent(`Fix the flaky test ${t.name}`)
))
```

`export const meta` 로 시작하고, 그 아래가 본문입니다. **평범한 자바스크립트**입니다 — `for`, `if`, `while` 다 됩니다. 그게 요점이죠.

### `meta` 는 순수 리터럴이어야 합니다

변수를 넣거나 함수를 부르면 안 됩니다.

```js
// ❌ 안 됩니다
export const meta = { name: buildName(), phases: PHASES }

// ✅ 이렇게
export const meta = { name: 'find-flaky-tests', phases: [{ title: 'Scan' }] }
```

**왜냐하면 실행하기 전에 읽어야 하기 때문입니다.** 워크플로를 돌리기 전에 사용자에게 "이런 걸 실행하려 합니다" 하고 보여줘야 하는데, 그걸 알려면 스크립트를 **정적으로** 읽어야 합니다. 함수 호출이 섞이면 실행해봐야 알 수 있죠. [추론]

## 쓸 수 있는 함수들

| 함수 | 무엇 |
|---|---|
| `agent(prompt, opts)` | 서브에이전트 하나. `schema` 를 주면 **검증된 객체**로 돌아옴 |
| `parallel(thunks)` | 동시 실행하고 **전부 기다림** |
| `pipeline(items, ...stages)` | 항목별로 단계를 통과시킴 |
| `phase(title)` | 진행 표시 그룹 |
| `log(msg)` | 사용자에게 진행 상황 표시 |
| `args` | 호출할 때 넘긴 값 (전역) |
| `budget` | 토큰 예산 (전역) |

`agent()` 의 `schema` 가 특히 유용합니다. JSON Schema 를 주면 자식이 **구조화된 출력을 강제**당하고, 반환값이 파싱된 객체로 옵니다. 1편에서 "답의 형태를 브리핑에 넣어라"고 했던 것의 기계적 버전입니다.

> **주의: `Date.now()`, `Math.random()`, 인자 없는 `new Date()` 를 못 씁니다.** 4편에서 볼 재개 캐시 때문입니다. 매번 값이 달라지면 캐시가 성립하지 않으니까요.

## 실제로 돌려봅시다

최소 프로브를 만들어 실행했습니다. 항목 2 개 × 단계 2 개 = 에이전트 4 개, 전부 `haiku` 에 "이 문자열을 그대로 반환하라" 수준의 사소한 작업입니다.

```js
export const meta = {
  name: 'probe-pipeline',
  description: 'Minimal probe to capture Workflow execution mechanics',
  phases: [
    { title: 'Stage1', detail: 'echo the word back' },
    { title: 'Stage2', detail: 'append the index' },
  ],
}

const SCHEMA = {
  type: 'object',
  properties: { value: { type: 'string' } },
  required: ['value'],
  additionalProperties: false,
}

log('probe start')
const items = ['alpha', 'beta']

const out = await pipeline(
  items,
  (item) => agent(
    `Return exactly the word: ${item}. Do not use any tools. Do not explain.`,
    { label: `s1:${item}`, phase: 'Stage1', schema: SCHEMA, model: 'haiku', effort: 'low' }
  ),
  (prev, item, i) => agent(
    `Return exactly this string: ${prev ? prev.value : 'null'}-${i}. Do not use any tools.`,
    { label: `s2:${item}`, phase: 'Stage2', schema: SCHEMA, model: 'haiku', effort: 'low' }
  )
)

log('probe done')
return { out, argsSeen: args, budgetTotal: budget.total }
```

결과입니다. [관찰]

```json
{"out":[{"value":"alpha-0"},{"value":"beta-1"}],
 "argsSeen":{"probe":"season2-investigation"},
 "budgetTotal":null,"budgetSpent":529052}
```

```
agent_count 4 · agents_done 4 · agents_error 0
subagent_tokens 99,579 · duration_ms 10,083
```

**10 초에 에이전트 4 개.** `args` 가 그대로 전달됐고, `budget.total` 은 예산 지시가 없어서 `null` 입니다.

## 디스크에 남는 것 — 디렉터리 둘, 산출물 셋

이게 이 편에서 가장 실용적인 부분입니다. 워크플로를 돌리면 **디렉터리 두 곳에 세 종류**의 산출물이 생깁니다.

```
~/.claude/projects/<slug>/<session-id>/
├── workflows/scripts/<meta.name>-<runId>.js     ← ① 스크립트 영속 사본
└── subagents/workflows/<runId>/
    ├── journal.jsonl                             ← ② 실행 저널 (4편의 주인공)
    ├── agent-<id>.jsonl                          ← ③ 에이전트별 트랜스크립트
    └── agent-<id>.meta.json
```

직접 확인해보세요.

```bash
find ~/.claude/projects -path '*workflows*' -name '*.js' | head -3
find ~/.claude/projects -name journal.jsonl | head -3
```

### ① 스크립트가 저장됩니다

인라인으로 넘긴 스크립트도 **파일로 남습니다.** 그래서 고쳐서 다시 돌릴 때 스크립트를 통째로 재전송할 필요가 없습니다 — 파일을 편집하고 `scriptPath` 로 가리키면 됩니다.

> **경로가 두 개라는 게 헷갈리는 지점입니다.** `.claude/workflows/<name>.js` 는 **미리 정의해둔** 워크플로의 위치고, 인라인 `script` 로 넘긴 것은 위처럼 **세션 디렉터리 안**에 사본이 남습니다. 시즌 1 의 9편에도 같은 구분이 적혀 있습니다. [관찰]

### ③ 에이전트들은 특별한 타입입니다

`meta.json` 을 열어보면 전부 똑같습니다. [관찰] (파일이 8 개인 건 같은 워크플로를 여러 번 돌려 같은 `runId` 디렉터리에 쌓였기 때문입니다.)

```json
{"agentType":"workflow-subagent","spawnDepth":1,"model":"haiku"}
```

두 가지가 눈에 띕니다.

**첫째, `workflow-subagent` 라는 전용 타입입니다.** 시즌 1 의 8편에서 봤듯 이 타입은 **`Skill`/`Agent`/`Workflow` 툴이 금지**됩니다. 워크플로 에이전트가 또 워크플로를 부르는 무한 재귀를 막는 것입니다.

제 프로브 에이전트들의 트랜스크립트는 9 줄뿐입니다. 언뜻 보면 툴을 한 번도 안 쓴 것처럼 보입니다.

```bash
W=$(dirname $(find ~/.claude/projects -name journal.jsonl | head -1))
f=$(ls "$W"/agent-*.jsonl | head -1)
python3 -c "
import json,collections
c=collections.Counter()
for l in open('$f'):
    if l.strip(): c[json.loads(l).get('type')]+=1
print(dict(c))"
```

```
{'user': 3, 'attachment': 4, 'assistant': 2}
```

**아홉 줄뿐입니다.** 그런데 이 집계로는 알 수 없는 게 있습니다 — **레코드 타입만 세기 때문에 `assistant` 레코드 *안의* 툴 호출은 안 보입니다.** 한 겹 더 들어가봅시다.

```bash
python3 -c "
import json,glob,collections
c=collections.Counter()
for p in glob.glob('$W/agent-*.jsonl'):
    for l in open(p):
        if not l.strip(): continue
        d=json.loads(l)
        if d.get('type')!='assistant': continue
        cc=(d.get('message') or {}).get('content')
        if isinstance(cc,list):
            for b in cc:
                if isinstance(b,dict) and b.get('type')=='tool_use': c[b.get('name')]+=1
print(dict(c))"
```

```
{'StructuredOutput': 8}
```

**에이전트 8 개가 각각 `StructuredOutput` 을 한 번씩 불렀습니다.** [관찰] `agent()` 에 `schema` 를 주면 자식이 **그 툴을 호출하도록 강제**되고, 그 인자가 곧 반환값이 됩니다. 1편에서 "답의 형태를 브리핑에 넣어라"고 했던 것의 기계적 구현입니다.

> **제가 처음엔 "`tool_use` 가 하나도 없다"고 썼습니다.** 위의 타입 집계만 보고 그렇게 판단했죠. 레코드 타입 집계는 **블록 안을 못 봅니다.** 시즌 1 의 4편에서 "응답 하나가 여러 줄로 쪼개진다"를 배웠는데, 그 반대편 함정(한 줄 안에 여러 블록)에 걸린 셈입니다.

**둘째, `spawnDepth: 1` 입니다.** 깊이 0 이 아닙니다.

> **깊이 0 이 아니라는 게 왜 의미가 있을까요?** 시즌 1 의 7편에서 본 중첩 상한이 **3** 이니, 워크플로는 시작부터 한 칸을 씁니다.
>
> 다만 **이 에이전트들은 `Agent` 툴 자체가 금지**돼 있어서(바로 위) 스스로 자식을 낳지는 못합니다. 그러니 실무적 의미는 "여유가 두 칸"이라기보다 **워크플로가 이미 한 계층을 소비한다**는 사실입니다.

## 완료 통지

워크플로가 끝나면 1편에서 본 `<task-notification>` 과 같은 경로로 옵니다. 다만 `<usage>` 필드가 다릅니다. [관찰]

```xml
<usage>
  <agent_count>4</agent_count>
  <agents_done>4</agents_done>
  <agents_error>0</agents_error>
  <agents_skipped>0</agents_skipped>
  <agents_empty_result>0</agents_empty_result>
  <subagent_tokens>99579</subagent_tokens>
  <tool_uses>4</tool_uses>
  <duration_ms>10083</duration_ms>
</usage>
```

**`<tool_uses>4</tool_uses>`** 가 바로 위에서 센 `StructuredOutput` 호출 4 건입니다. 하네스가 직접 확인해주는 셈이죠. 캐시로 재생된 회차는 이 값이 **0** 입니다 — 4편에서 "실제로 몇 개가 돌았나"를 판별하는 가장 깔끔한 근거입니다. [관찰]

`agents_empty_result` 라는 필드가 있는 게 재밌습니다. **빈 결과를 돌려준 에이전트를 따로 셉니다.** 6편에서 볼 "덜 전달되는" 실패가 흔하다는 뜻이겠죠. [추론]

그리고 통지에 이런 안내가 붙습니다. [관찰]

```
Per-agent results: .../journal.jsonl — one {"type":"result",...} line per completed agent.
If the result above is empty or unexpected, Read this file BEFORE diagnosing.
```

**"결과가 이상하면 진단하기 전에 저널부터 읽어라."** 하네스가 직접 그렇게 시킵니다. 4편의 주제입니다.

## 언제 Workflow 를 쓰나

| 상황 | 선택 |
|---|---|
| 한두 개 위임, 판단이 유연해야 함 | **`Agent` 툴** (1·2편) |
| 항목이 여럿이고 처리가 동일함 | **`Workflow`** |
| 조건 분기·반복이 필요함 | **`Workflow`** — 코드가 훨씬 정확합니다 |
| 같은 걸 여러 번 돌려야 함 | **`Workflow`** — 재개 캐시가 듣습니다 (4편) |
| 중간 결과를 부모가 봐야 판단 가능 | `Agent` 툴 — 워크플로는 부모를 거치지 않습니다 |

> **`Workflow` 는 사용자가 명시적으로 요청해야 부를 수 있습니다.** 툴 설명에 그렇게 못 박혀 있습니다 — 에이전트를 수십 개 띄울 수 있으니 비용이 크기 때문입니다. "워크플로로 해줘" 같은 말이 필요합니다.

## 정리

- **`Workflow` 는 플러그인이 아니라 빌트인**입니다. 대조군을 낀 따옴표 리터럴 검사로 확인했습니다.
- 모델이 조율할 때의 세 가지 문제 — **재현 불가, 반복·분기 어려움, 중간 결과가 부모 컨텍스트로 돌아옴** — 을 코드로 푸는 도구입니다.
- 스크립트는 평범한 JS 지만 **`meta` 는 순수 리터럴**이어야 하고, **`Date.now()`/`Math.random()` 은 금지**입니다.
- 실행하면 **스크립트 사본 · 실행 저널 · 에이전트별 트랜스크립트** 가 디스크에 남습니다.
- 워크플로 에이전트는 **`workflow-subagent`** 타입이고 **`spawnDepth: 1`** 에서 시작합니다 — 중첩 여유가 두 칸뿐입니다.
- 하네스가 **"결과가 이상하면 저널부터 읽어라"** 고 직접 안내합니다.

## 확인 못 한 것

1. **`bundledWorkflows`** — 미리 정의된 워크플로 레지스트리가 코드에 있지만, 따옴표 리터럴로는 0 건이라 실제로 무엇이 번들돼 있는지 확인하지 못했습니다.
2. **원격 실행** — 출력 스키마에 `remote_launched` 와 `sessionUrl` 이 있지만 재현하지 못했습니다.
3. `meta` 가 순수 리터럴이어야 하는 **이유**는 제 추측입니다. 실행 전 정적 분석이 필요해 보이지만 코드로 확인하지는 않았습니다. [추론]
4. 동시 실행 상한(`min(16, CPU-2)`)과 생애 총량(1000)은 문서에 있으나 **직접 부딪혀보지는 않았습니다.**

다음 편에서는 저널을 열어봅니다. **`pipeline` 과 `parallel` 이 실제로 어떻게 다른지**, 그리고 **재개 캐시가 0 토큰·10ms 로 도는 것과 그게 언제 깨지는지**를 실측으로 봅니다.

> 이전 편: [2편. 격리의 스펙트럼](./02-isolation-spectrum.md)
> 다음 편: [4편. Workflow ② — pipeline vs parallel, 그리고 재개 캐시](./04-workflow-patterns.md)
