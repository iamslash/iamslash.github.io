# 5편. Tool — 모델은 함수를 부르지 않는다

> 시리즈: Claude Code 내부 구조 (builtin 기준, v2.1.243)
> 이 편에서 배우는 것: 툴 정의의 실제 모양, 에러가 예외가 아니라 대화로 돌아오는 이유, **툴 목록이 고정이 아니라는 것**, 그리고 권한 규칙이 판단되는 순서.

4편에서 루프가 툴을 실행하는 걸 봤습니다. 이제 툴 자체를 봅니다.

## 툴 정의는 키 세 개뿐이다

모델에게 전달되는 툴 정의는 놀랄 만큼 단순합니다. **정확히 세 개 키**입니다. [관찰]

```json
{ "name": "...", "description": "...", "input_schema": { ... } }
```

Anthropic Messages API 표준 그대로입니다. Claude Code 만의 확장 필드는 없습니다.

캡처한 `Read` 툴의 실제 정의 전문입니다. [관찰]

```json
{
 "name": "Read",
 "description": "Reads a file from the local filesystem.\n\n- `file_path` must be an absolute path.\n- Reads up to 2000 lines by default.\n- When you already know which part of the file you need, only read that part...\n- Results are returned using cat -n format, with line numbers starting at 1\n- Do NOT re-read a file you just edited to verify — Edit/Write would have errored if the change failed, and the harness tracks file state for you.",
 "input_schema": {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
   "file_path": {"description":"The absolute path to the file to read","type":"string"},
   "offset": {"description":"The line number to start reading from...","type":"integer","minimum":0,"maximum":9007199254740991},
   "limit": {"description":"The number of lines to read...","type":"integer","exclusiveMinimum":0},
   "pages": {"description":"Page range for PDF files (e.g., \"1-5\")...","type":"string"}
  },
  "required": ["file_path"],
  "additionalProperties": false
 }
}
```

여기서 두 가지를 짚습니다.

**첫째, `description` 이 곧 프롬프트입니다.** 위 설명을 다시 읽어보세요. `"Do NOT re-read a file you just edited to verify"` — 이건 스펙이 아니라 **행동 지시**입니다. 툴 설명란은 사실상 그 툴 전용 시스템 프롬프트입니다.

얼마나 그러냐면, `Workflow` 툴 하나의 설명이 **19,290 자**입니다. [관찰]

```bash
jq -r '.body.tools[] | "\(.description|length)\t\(.name)"' /tmp/cc-lab/capture/req02.json | sort -rn | head -5
```

**둘째, `maximum: 9007199254740991`** 은 자바스크립트의 `Number.MAX_SAFE_INTEGER` 입니다. 스키마가 JS 로 생성됐다는 흔적이 그대로 남아 있습니다.

## 왕복 — 에러도 대화로 돌아온다

0편에서 본 왕복을 실제 레코드로 확인합시다.

**성공하면** [관찰]

```json
{"type":"tool_result",
 "tool_use_id":"toolu_017rMwt1uCwR5wt746RevkZ1",
 "content":"=== branch ===\nmain\n…",
 "is_error":false}
```

**실패하면** [관찰]

```json
{"type":"tool_result",
 "tool_use_id":"toolu_01QDujUrGnhLcnotdRbvdNWN",
 "content":"Exit code 1\nTraceback (most recent call last):\n  File \"<stdin>\", line 3, in <module>\nOSError: [Errno 9] Bad file descriptor",
 "is_error":true}
```

**형태가 같습니다.** 실패는 예외로 던져지지 않습니다. `is_error: true` 가 붙은 채로 **똑같이 대화에 들어갑니다.**

> 이게 Claude Code 가 스스로 고쳐나가는 것처럼 보이는 이유입니다. 명령이 실패하면 그 스택 트레이스가 **다음 요청의 입력이 됩니다.** 모델은 에러 메시지를 읽고 다음 수를 둡니다. 예외 처리가 아니라 **대화**입니다.

트랜스크립트 레코드에는 API 로 나가는 블록 말고 `toolUseResult` 라는 형제 필드가 하나 더 있어서, 구조화된 원본을 따로 보관합니다. [관찰]

```bash
cd ~/.claude/projects
python3 - <<'PY'
import json,glob,os
p=sorted(glob.glob('*/*.jsonl'), key=os.path.getmtime)[-1]
for l in open(p):
    d=json.loads(l)
    c=(d.get('message') or {}).get('content')
    if isinstance(c,list):
        for b in c:
            if isinstance(b,dict) and b.get('type')=='tool_result':
                print('is_error=',b.get('is_error'),
                      '| content:',str(b.get('content'))[:70])
                print('  toolUseResult:',str(d.get('toolUseResult'))[:70]); raise SystemExit
PY
```

## 반전 — 툴 목록은 고정이 아니다

"Claude Code 의 기본 툴은 Read, Write, Edit, Bash, Grep, Glob…" 이라고 설명하는 글이 많습니다. **제 설치본에서는 틀립니다.**

2편에서 캡처한 툴 목록에 `Grep` 과 `Glob` 이 없었던 걸 기억하시나요? 실제로 쓰이는지 세어봅시다.

```bash
cd ~/.claude/projects
python3 - <<'PY'
import json,glob,collections,os,time
c=collections.Counter(); cutoff=time.time()-3*86400
for p in glob.glob('*/*.jsonl'):
    if os.path.getmtime(p)<cutoff: continue
    for l in open(p,errors='ignore'):
        try: o=json.loads(l)
        except Exception: continue
        cc=(o.get('message') or {}).get('content')
        if isinstance(cc,list):
            for b in cc:
                if isinstance(b,dict) and b.get('type')=='tool_use': c[b.get('name')]+=1
for k,v in c.most_common(8): print(f'{v:7d}  {k}')
print('---')
for t in ('Grep','Glob','TodoWrite','ExitPlanMode','MultiEdit','SlashCommand'):
    print(f'{c.get(t,0):7d}  {t}')
PY
```

최근 3일 제 세션의 결과입니다. [관찰]

```
  23475  Bash
   4804  Edit
   2225  Read
   1016  mcp__linear__save_issue
    996  Write
    548  Agent
    535  ToolSearch
    152  SendMessage
---
      0  Grep
      0  Glob
      0  TodoWrite
      0  ExitPlanMode
      0  MultiEdit
      0  SlashCommand
```

**`Grep`, `Glob`, `TodoWrite` 는 단 한 번도 쓰이지 않았습니다.** 대신 `Bash` 가 23,475 번으로 압도적입니다.

바이너리에서 이유를 찾을 수 있습니다. `Bash` 툴의 설명문을 만드는 함수에 분기가 있습니다. [관찰]

```js
function S5s(e){
  let u = ou() ? "`cat`, `head`, `tail`, `sed`, `awk`, or `echo`"
              : "`find`, `grep`, `cat`, `head`, `tail`, `sed`, `awk`, or `echo`";
  s.push(`- IMPORTANT: Avoid using this tool to run ${u} commands, …`)
}
```

게이트가 켜지면 회피 목록에서 **`find` 와 `grep` 이 빠집니다.** 즉 "Bash 로 grep 하지 마라"는 지시가 사라지고, 대신 `Grep`/`Glob` 툴이 목록에서 제거됩니다. 파일 검색을 **Bash 로 하도록 전환**하는 것입니다.

제가 캡처한 `Bash` 설명문에는 `find`/`grep` 이 회피 목록에서 빠져 있었고, 이는 `Grep`/`Glob` 툴이 없는 분기와 정확히 일치했습니다. [관찰]

> **중요: 여러분 계정에서는 다를 수 있습니다.** [추론] 이 게이트는 서버 사이드 실험으로 배포되는 것으로 보입니다(디버그 로그에 `source: growthbook` 이 보입니다). **그래서 "기본 툴 목록"을 외우지 말고 직접 확인하세요.**

내 세션의 실제 툴 목록을 보는 가장 확실한 방법은 0편의 로컬 싱크입니다.

```bash
jq -r '.body.tools[].name' /tmp/cc-lab/capture/req02.json | sort
```

### 인용하면 안 되는 함정

바이너리 안에 이런 배열이 있습니다.

```
BUILTIN_TOOL_NAMES=["Bash","Read","Write","Edit","Glob","Grep","NotebookEdit","WebFetch",
"WebSearch","Task","TodoWrite","TaskCreate","TaskUpdate","TaskGet","TaskList","TaskStop",
"Skill","REPL","JavaScript","AskUserQuestion","ToolSearch","SendUserMessage"]
```

이름이 그럴듯해서 "이게 공식 목록"이라고 인용하기 딱 좋습니다. **하지만 아닙니다.** [관찰]

- 이건 런타임 레지스트리가 아니라 **문서 블롭 안의 상수**입니다.
- `REPL`, `JavaScript`, `SendUserMessage` 같이 **다른 제품 표면 전용** 툴이 섞여 있습니다.
- 실제 캡처된 요청과 일치하지 않습니다.

> **교훈:** 바이너리에서 그럴듯한 문자열을 찾았다고 그게 실제로 쓰이는 건 아닙니다. **와이어에 나가는 것을 봐야 합니다.**

## 권한 시스템

툴은 아무거나 실행되지 않습니다. 권한 모드가 먼저 걸립니다.

문서에는 네 가지가 나오는데, 바이너리에는 **다섯 번째**가 있습니다. [관찰]

```bash
B=$(ls -d ~/.local/share/claude/versions/* | tail -1)
LC_ALL=C strings -n 4 "$B" \
  | grep -oE '"(default|acceptEdits|bypassPermissions|plan|dontAsk)"' | sort | uniq -c
```

```
1013 "default"      219 "plan"      96 "bypassPermissions"
  48 "acceptEdits"   41 "dontAsk"    ← 문서에 잘 안 나오는 것
```

| 모드 | 동작 |
|---|---|
| `default` | 위험한 작업마다 물어봄 |
| `acceptEdits` | 파일 편집은 자동 승인 |
| `plan` | 계획만 세우고 실행 안 함 (9편) |
| `bypassPermissions` | 전부 승인 — **실험용 디렉터리에서만** |
| `dontAsk` | 묻지 않음 |

### 설정은 어디서 오나

바이너리의 병합 순서(낮은 우선순위 → 높은 우선순위)입니다. [관찰]

```js
["userSettings", "projectSettings", "localSettings", "flagSettings", "policySettings"]
```

이걸 뒤집으면 공식 문서의 우선순위와 정확히 일치합니다. [문서]

1. **Managed settings** — 조직이 MDM 으로 내리는 것 (macOS: `/Library/Application Support/ClaudeCode`)
2. **명령행** — `claude --settings`
3. **프로젝트 로컬** — `.claude/settings.local.json` (커밋 안 함)
4. **프로젝트 공유** — `.claude/settings.json` (커밋함)
5. **사용자** — `~/.claude/settings.json`

### 규칙 문법

바이너리의 **검증 에러 메시지**가 문법을 그대로 알려줍니다. [관찰]

| 규칙 | 의미 |
|---|---|
| `Bash(npm run:*)` | 접두사 매칭 (**레거시**) |
| `Bash(npm run *)` | 와일드카드 매칭 (권장) |
| `Read(*.ts)` · `Read(src/**)` | glob 파일 매칭 |
| `mcp__github__get_*` | MCP 는 **괄호 패턴 미지원**, 이름에 직접 `*` |

실제 에러 문구들입니다.

```
"The :* pattern must be at the end"
"Move :* to the end for prefix matching, or use * for wildcard matching"
"MCP rules do not support patterns in parentheses"
"Tool names must start with uppercase"
"Mismatched parentheses"
```

`Edit(경로)` 규칙은 **모든 편집 툴**(`NotebookEdit` 포함)을, `Read(경로)` 는 모든 읽기 툴을 커버합니다. 툴 이름 하나만 막으면 우회된다는 뜻이 아니니 안심해도 됩니다.

### 직접 실험해보기

```bash
mkdir -p /tmp/permlab && cd /tmp/permlab
cat > settings.json <<'EOF'
{"permissions":{"deny":["Bash(curl:*)","Read(./secret.txt)"],"allow":["Bash(echo:*)"]}}
EOF
echo "top-secret-value" > secret.txt
claude --settings ./settings.json --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  -p "1) run: echo allowed-ok  2) run: curl https://example.com  3) Read ./secret.txt"
```

결과입니다. [관찰]

1. `echo allowed-ok` → **프롬프트 없이 실행됨**
2. `curl` → `Permission to use Bash with command curl https://example.com has been denied.`
3. Read → `File is in a directory that is denied by your permission settings.`

> **주의 [문서]:** `permissions.allow` 와 `additionalDirectories` 는 **workspace trust 를 수락한 뒤에만** 적용됩니다. 반면 `deny` 와 `ask` 는 즉시 적용됩니다. 보안 관점에서 올바른 기본값입니다 — 막는 건 바로 듣고, 여는 건 확인을 거칩니다.

## MCP 툴은 특별하지 않다

MCP 서버가 제공하는 툴은 `mcp__<서버>__<툴>` 이름을 갖습니다. 그런데 **모델 입장에서는 builtin 과 구조적으로 아무 차이가 없습니다.** [관찰]

```js
{ name: e, isMcp: e.startsWith("mcp__"), … }
userFacingName: () => o ? `${t} (MCP)` : t
```

**같은 `tools` 배열에 그냥 섞여 들어갑니다.** 구분은 (1) 이름 접두사, (2) UI 표시할 때 `(MCP)` 를 붙이는 것뿐입니다.

제 세션 통계에서 `mcp__linear__save_issue` 가 1,016 번으로 `Write` 보다 많이 쓰인 게 보이시죠. 모델에게는 그냥 툴 하나입니다.

> **유용한 통제 실험 하나.** 어떤 툴이 builtin 인지 플러그인이 준 건지 헷갈릴 때, 플러그인 툴은 반드시 `mcp__plugin_<이름>__*` 형태입니다. 그리고 바이너리에 이름이 있으면 builtin 입니다. [관찰]
>
> ```bash
> B=$(ls -d ~/.local/share/claude/versions/* | tail -1)
> for t in CronCreate Workflow Monitor EnterWorktree; do
>   echo "$t $(LC_ALL=C grep -ac "\"$t\"" "$B")"; done
> # 전부 0 보다 큼 → builtin
> ```

## 툴 두 개의 속사정

### `Grep` 은 왜 ripgrep 인가

추측이 아닙니다. **ripgrep 이 바이너리에 통째로 들어 있습니다.** [관찰]

```bash
B=$(ls -d ~/.local/share/claude/versions/* | tail -1)
LC_ALL=C strings -n 4 "$B" \
  | grep -o 'ripgrep::[a-z_:]*\|@vscode/ripgrep\|RIPGREP_CONFIG_PATH\|grep_searcher::[a-z_:]*\|\.rgignore' \
  | sort -u
```

```
.rgignore
@vscode/ripgrep
grep_searcher::searchergeneric
grep_searcher::searcher::coresearcher
RIPGREP_CONFIG_PATH
ripgrep::flags::config
ripgrep::flags::hiargs
ripgrep::haystackmid
ripgrep::search
```

> 문자열이 조금씩 뭉개져 보이는 건 정상입니다. 바이너리에서 뽑은 것이라 인접한 문자열이 붙어 나옵니다. `grep -i ripgrep` 으로 넓게 잡으면 더 심하니, 위처럼 토큰을 좁혀 잡는 편이 읽기 좋습니다.

Rust ripgrep 의 내부 문자열까지 그대로 있습니다. 여기서 두 가지가 설명됩니다.

- **`.gitignore` 를 자동으로 존중합니다.** ripgrep 의 기본 동작입니다.
- **lookahead/lookbehind 를 못 씁니다.** ripgrep 의 기본 엔진이 유한 오토마타 기반이라 원리적으로 지원하지 않습니다.

### `Read` 는 파일 상태를 추적한다

`Edit` 을 쓰기 전에 반드시 `Read` 를 해야 하는 이유입니다. 바이너리에 가드 문자열이 있습니다. [관찰]

```
"File has not been read yet. Read it first before writing to it."
"File has been modified since read, either by the user or by a linter.
 Read it again before attempting to write it."
```

내부 상태 키: `readFileState`, `fileStates`, `userModified`, `originalFileContents`

> **왜 이런 장치가 필요할까요?** 모델은 파일을 "기억"으로만 알고 있습니다. 그 사이에 여러분이 에디터에서 고쳤거나 린터가 포맷했다면, 모델이 기억하는 내용은 낡은 것입니다. 그 상태로 `Edit` 을 하면 **엉뚱한 곳을 고치거나 남의 변경을 덮어씁니다.** 그래서 하네스가 읽은 시점을 기록해두고, 어긋나면 거부합니다.

## 정리

- 툴 정의는 **`name` / `description` / `input_schema` 세 키뿐**입니다. API 표준 그대로입니다.
- **`description` 이 곧 프롬프트입니다.** `Workflow` 는 설명만 19,290 자입니다.
- **에러는 예외가 아니라 대화로 돌아옵니다.** `is_error: true` 가 붙은 `tool_result` 로 들어가고, 모델이 그걸 읽고 복구합니다.
- **툴 목록은 고정이 아닙니다.** 제 설치본에는 `Grep`/`Glob`/`TodoWrite` 가 없고 `Bash` 가 그 자리를 대신합니다. 여러분 계정은 다를 수 있으니 **직접 캡처해서 확인하세요.**
- 바이너리의 `BUILTIN_TOOL_NAMES` 는 **인용하면 안 되는 함정**입니다. 와이어를 보세요.
- 권한 모드는 다섯 개(`dontAsk` 포함), 설정은 다섯 소스가 병합되며 **managed 가 최우선**입니다.
- **MCP 툴은 같은 배열에 섞입니다.** 모델에게는 구조적 차이가 없습니다.
- `Grep` 은 진짜 ripgrep 이고, `Read` 는 `Edit` 안전을 위해 파일 상태를 추적합니다.

## 확인 못 한 것

1. **`Grep`/`Glob` 을 없애는 게이트의 정확한 조건.** 코드상 분기(`ou() && Ks()`)는 찾았지만, 어떤 조합에서 켜지는지는 특정하지 못했습니다.

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

2. `auto` 라는 여섯 번째 권한 모드가 빌드 게이트된 모듈로 존재하지만, 활성화해보지는 못했습니다.
3. `AskUserQuestion` 과 `ExitPlanMode` 가 제 캡처에 없는 것은 `-p` 비대화형 모드 때문으로 보입니다. 트랜스크립트에는 `AskUserQuestion` 이 34 회 나옵니다. [추론]

다음 편에서는 **훅**을 봅니다. 2편에서 셸 스크립트의 표준출력이 모델 컨텍스트에 그대로 들어가는 걸 봤죠. 그게 어디까지 가능한지 — 툴 실행을 막고, 턴이 끝나는 것도 막을 수 있습니다.

> 이전 편: [4편. Agent loop — while 루프 하나가 전부다](./04-agent-loop.md)
> 다음 편: [6편. Hook — 하네스에 내 코드를 꽂는 자리](./06-hooks.md)
