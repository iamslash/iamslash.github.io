# 1편. 엔터를 치면 무슨 일이 일어나는가

> 시리즈: Claude Code 내부 구조 (builtin 기준, v2.1.243)
> 이 편에서 배우는 것: 입력의 **첫 글자**가 완전히 다른 경로를 고른다는 것, 슬래시 커맨드가 모델을 아예 부르지 않을 수도 있다는 것, 그리고 `@파일` 이 툴 호출이 **아니라는** 것.

0편에서 Claude Code 의 뼈대가 `while` 루프 하나라는 걸 봤습니다. 이제 그 루프의 **입구**를 봅니다.

여러분이 프롬프트를 치고 엔터를 누릅니다. 그 순간 Claude Code 가 가장 먼저 하는 일은 API 호출이 아닙니다. **첫 글자를 봅니다.**

```
> 로그인 버그 고쳐줘        ← 평문
> /model                    ← 슬래시
> !git status               ← 느낌표
> #앞으로 타입힌트 꼭 써     ← 샵
> @auth.py 이거 봐줘        ← 골뱅이
```

다섯 갈래는 **서로 다른 코드 경로**로 갑니다. 어떤 건 API 를 아예 호출하지 않고, 어떤 건 API 호출 전에 여러분 컴퓨터에서 명령을 실행합니다.

## 첫 글자가 모드를 정한다

| 입력 | 트랜스크립트에 남는 것 | 모델을 부르나? |
|---|---|---|
| 평문 | `type:"user"` 레코드 | 부른다 |
| `/명령` (로컬 실행형) | `<command-name>` + `<local-command-stdout>` | **안 부른다** |
| `/명령` (프롬프트 확장형) | `type:"user"`, 본문이 펼쳐진 채로 | 부른다 |
| `!명령` | `<bash-input>` + `<bash-stdout>` / `<bash-stderr>` | 보통 안 부른다 |
| `#메모` | `<user-memory-input>` | — |
| `@파일` | `attachment` 레코드 + **선(先)읽기 합성 메시지** | 부른다 |

하나씩 봅시다.

## 평문 — 가장 단순한 경로

평문은 그냥 user 메시지가 됩니다. 다만 트랜스크립트에는 **어디서 온 입력인지**가 같이 기록됩니다.

```bash
cd ~/.claude/projects
python3 - <<'PY'
import json,glob,collections
c=collections.Counter()
for p in glob.glob('*/*.jsonl'):
    try:
        for l in open(p):
            if not l.strip(): continue
            d=json.loads(l)
            if d.get('promptSource'): c[d['promptSource']]+=1
    except Exception: pass
print(dict(c.most_common()))
PY
```

제 머신에서는 이렇게 나왔습니다. [관찰]

```
{'typed': 6246, 'system': 1417, 'queued': 425, 'sdk': 234, 'suggestion_accepted': 80}
```

- `typed` — 사람이 직접 친 것
- `queued` — 모델이 일하는 동안 미리 쳐놓은 것
- `system` — 사람이 아니라 하네스가 만들어 넣은 것 (훅 출력, 서브에이전트 완료 알림 등)
- `sdk` — 프로그램에서 SDK 로 넣은 것

`system` 이 1,417 건이나 된다는 게 눈에 띕니다. **여러분이 치지 않은 user 메시지가 대화에 계속 끼어들고 있다**는 뜻입니다. 6편(Hook)과 7편(서브에이전트)에서 그 정체를 봅니다.

## `/` 슬래시 — 절반은 모델을 부르지도 않는다

가장 오해가 많은 지점입니다. 슬래시 커맨드는 **하나의 메커니즘이 아닙니다.**

빌트인 커맨드는 102 개가 있고, 내부적으로 세 가지 타입으로 나뉩니다. [관찰]

- **`local-jsx`** (~78개) — 터미널 UI 를 띄웁니다. `/model`, `/config`, `/resume`, `/permissions`, `/agents` …
- **`local`** (~37개) — 로컬 함수를 실행합니다. `/clear`, `/compact`, `/context`, `/recap` …
- **`prompt`** (3개) — `init`, `insights`, `team-onboarding`. **이것만** 프롬프트 텍스트로 펼쳐집니다.

앞의 둘, 즉 **대부분의 슬래시 커맨드는 모델을 다시 부르지 않습니다.** 로컬에서 실행하고 결과를 대화 기록에 남길 뿐입니다.

### 직접 확인해봅시다

`/model` 을 쳤을 때 트랜스크립트에 뭐가 남는지 봅니다.

```bash
cd ~/.claude/projects
python3 - <<'PY'
import json,glob,re
for p in glob.glob('*/*.jsonl'):
    try: rows=[json.loads(l) for l in open(p) if l.strip()]
    except Exception: continue
    for i,d in enumerate(rows):
        c=(d.get('message') or {}).get('content') if d.get('message') else d.get('content')
        t=c if isinstance(c,str) else ''.join(b.get('text','') for b in c if isinstance(b,dict)) if isinstance(c,list) else ''
        if t and '<command-name>/model</command-name>' in t:
            for r in rows[i:i+2]:
                rc=(r.get('message') or {}).get('content') if r.get('message') else r.get('content')
                rt=rc if isinstance(rc,str) else ''.join(b.get('text','') for b in rc if isinstance(b,dict)) if isinstance(rc,list) else ''
                print('type=',r.get('type'),'subtype=',r.get('subtype'),'::',repr((rt or '')[:110]))
            raise SystemExit
PY
```

```
type= system subtype= local_command :: '<command-name>/model</command-name>\n            <command-message>model</command-message>\n            <command-'
type= system subtype= local_command :: '<local-command-stdout>Kept model as \x1b[1mOpus 5 (1M context)\x1b[22m</local-command-stdout>'
```

(첫 줄은 110 자에서 잘렸습니다. 원래는 `<command-args></command-args>` 로 끝납니다.)

`<local-command-stdout>` 안의 문자열에 **ANSI 이스케이프 코드(`\x1b[1m`)** 가 그대로 들어 있는 게 보이시나요? 이건 터미널에 굵은 글씨로 출력하려고 붙인 것입니다. 즉 **이 텍스트는 모델에게 보내려고 만든 게 아니라 사람 화면에 뿌리려고 만든 것**입니다.

### "정말 모델을 안 부르나?" — 세어보기

주장을 확인하는 가장 좋은 방법은, `<local-command-stdout>` 바로 **다음**에 오는 레코드가 뭔지 전부 세어보는 것입니다. 모델을 불렀다면 `assistant` 레코드가 따라와야 합니다.

```bash
cd ~/.claude/projects
python3 - <<'PY'
import json,glob,collections
nxt=collections.Counter()
for p in glob.glob('*/*.jsonl'):
    try: rows=[json.loads(l) for l in open(p) if l.strip()]
    except Exception: continue
    for i,d in enumerate(rows):
        c=(d.get('message') or {}).get('content') if d.get('message') else d.get('content')
        t=c if isinstance(c,str) else ''.join(b.get('text','') for b in c if isinstance(b,dict)) if isinstance(c,list) else ''
        if t and '<local-command-stdout>' in t:
            n=rows[i+1] if i+1<len(rows) else None
            nxt[n.get('type') if n else '<EOF>']+=1
for k,v in nxt.most_common(): print(f'{v:5d}  {k}')
PY
```

제 머신의 전체 세션(총 221 건)에서: [관찰]

```
  111  attachment
   57  file-history-snapshot
   21  user
   12  last-prompt
    9  queue-operation
    6  assistant
    5  system
```

`assistant` 는 **6 건**뿐입니다. 그리고 그 6 건을 열어보면 전부 `/login` 과 `/mcp` 였습니다 — 인증이 끊겨서 작업 도중에 로그인한 뒤, **원래 하던 작업이 이어진** 경우입니다. 슬래시 커맨드 *때문에* 모델이 불린 게 아닙니다.

> **결론:** 대부분의 슬래시 커맨드는 **API 를 한 번도 호출하지 않습니다.** `/model` 로 모델을 바꾸든 `/context` 로 컨텍스트를 보든, 그건 여러분 터미널 안에서 끝나는 일입니다.

### 남은 수수께끼 하나

기록 형태가 두 가지입니다. `type:"system"` + `subtype:"local_command"` 인 것도 있고, `type:"user"` 인 것도 있습니다. 같은 `/model` 이 양쪽으로 다 나타나고, 버전과도 상관이 없었습니다(v2.1.173 에도 둘 다 있음). **어느 쪽이 언제 선택되는지는 확인하지 못했습니다.** [확인 못 함]

## `!` — 셸 명령을 바로 실행한다

`!` 로 시작하면 그 줄은 셸에서 실행되고, 입력과 출력이 대화 기록에 남습니다.

```bash
cd ~/.claude/projects
grep -o -- 'bash-input' */*.jsonl | wc -l     # 제 머신: 27
```

실제 레코드는 이렇게 생겼습니다. [관찰]

```json
{"type": "user",
 "message": {"role": "user", "content": "<bash-input>pwd</bash-input>"},
 "version": "2.1.173", ...}
```

이어서 `<bash-stdout>` / `<bash-stderr>` 레코드가 붙습니다. 번들 코드에도 그대로 보입니다. [관찰]

```js
return { messages:[..., d({content:`<bash-stdout>${J}</bash-stdout><bash-stderr>${a(G)}</bash-stderr>`})],
         shouldQuery: M }
```

여기 `shouldQuery` 가 중요합니다. **이 값이 false 면 모델을 부르지 않습니다.** `!ls` 는 그냥 로컬에서 실행되고 결과만 기록에 남고 턴이 끝납니다.

> 이게 왜 쓸모 있냐면 — 결과가 **대화 기록에 남기 때문**입니다. 다음 턴에 모델을 부를 때 그 출력이 이력에 포함되어 같이 전송됩니다. "명령 결과를 모델에게 보여주되, 지금 당장 대답은 시키지 않는" 용도입니다.

## `#` — 메모리에 적는다

`#` 로 시작하면 `<user-memory-input>` 태그가 붙어 `CLAUDE.md` 같은 메모리 파일에 반영됩니다. [문서]

> **정직하게 밝힙니다.** 이 태그를 제 트랜스크립트에서 찾아봤더니 **이 글을 쓰는 세션 하나에서만** 나왔습니다. 제가 조사하면서 태그 이름을 인용한 것이 잡힌 것이지, 실제 `#` 입력 기록이 아니었습니다. 바이너리 안에 문자열이 존재하는 것까지는 확인했지만, **실제 동작은 관찰하지 못했습니다.** [확인 못 함]

```bash
# 바이너리에 태그가 존재하는지만 확인
B=$(ls -d ~/.local/share/claude/versions/* | tail -1)
LC_ALL=C strings -n 4 "$B" | grep -o '<user-memory-input>' | head -1
```

## `@파일` — 이 편의 반전

`@auth.py` 를 쓰면 모델이 Read 툴을 호출해서 파일을 읽는다고 생각하기 쉽습니다. **아닙니다.**

로컬 싱크로 `claude -p "Look at @magic.ts and reply PONG"` 의 실제 `messages` 배열을 캡처하면 이렇게 나옵니다. [관찰]

```
messages[0] role=user  (문자열)
  "<system-reminder>
   Called the Read tool with the following input: {"file_path":"/.../magic.ts"}
   </system-reminder>"

messages[1] role=user  (블록 배열)
  [0] "<system-reminder>
       Result of calling the Read tool:
       1  export const MAGIC = 42;
       </system-reminder>"
  [1] <system-reminder> 에이전트 목록
  [2] <system-reminder> 스킬 목록
  [3] <system-reminder> CLAUDE.md + 오늘 날짜
  [4] "Look at @magic.ts and reply PONG"
```

`tool_use` 블록도, `tool_result` 블록도 없습니다. 대신 **"Read 를 호출했고 결과는 이거였다"고 *말하는* 평범한 텍스트**가 들어 있습니다.

> **무슨 일이 벌어진 걸까요?**
> 하네스가 API 를 호출하기 **전에** 파일을 직접 읽고, 대화 이력에 "이미 읽은 것처럼" 텍스트를 심은 것입니다. 모델 입장에서는 정신을 차려보니 파일 내용이 이미 이력에 있는 상태입니다.

이게 왜 중요할까요?

1. **왕복이 한 번 줄어듭니다.** 진짜 툴 호출이었다면 `요청 → tool_use → 실행 → tool_result → 재요청` 으로 API 를 두 번 불러야 합니다. `@` 는 처음부터 넣어버리니 한 번이면 됩니다.
2. **권한 확인을 거치지 않습니다.** 여러분이 명시적으로 `@` 를 쳤으니 승인한 것으로 봅니다.
3. **모델이 거절할 수 없습니다.** 툴 호출이라면 모델이 "안 읽어도 될 것 같다"고 판단할 여지가 있지만, `@` 는 무조건 들어갑니다.

## 보너스 — 커스텀 슬래시 커맨드와 `$1` 함정

`.claude/commands/` 에 마크다운 파일을 두면 나만의 커맨드가 됩니다.

```markdown
---
description: Greet with args
argument-hint: <name>
---
Say hello to $1. The full args were: $ARGUMENTS.
Current branch: !`git branch --show-current`
```

`/greet World` 로 실행하면 이렇게 펼쳐집니다. [관찰]

```
Say hello to $1. The full args were: World.
Current branch: main
```

두 가지가 눈에 띕니다.

**첫째, `` !`git branch --show-current` `` 가 실제로 실행되어 `main` 으로 바뀌었습니다.** API 호출 전에 여러분 셸에서 돌아갑니다.

**둘째, `$1` 이 치환되지 않고 그대로 남았습니다.** 오타가 아닙니다. 번들의 실제 치환 코드를 보면 이유가 나옵니다. [관찰]

```js
e = e.replace(/\$(\d+)(?!\w)/g, (u,d)=>{
      let p = parseInt(d,10);
      if (i[p]===void 0) return u;      // ← 없으면 "$1" 을 그대로 둔다
      return c=!0, s(i[p]);
    });
```

`i` 는 인자 배열이고 **0-인덱스**입니다. 즉 `$1` 은 `i[1]` — **두 번째** 인자입니다.

| 표기 | 가리키는 것 | `/greet World` 결과 |
|---|---|---|
| `$ARGUMENTS` | 인자 문자열 전체 | `World` |
| `$0` | `i[0]` | `World` |
| **`$1`** | **`i[1]`** | **치환 안 됨** |

> **셸에서 오신 분이 반드시 밟는 지뢰입니다.** 셸의 `$1` 은 첫 번째 인자지만, 여기서는 **두 번째**입니다. 첫 번째를 원하면 `$0` 또는 `$ARGUMENTS[0]` 을 쓰세요.

친절한 점 하나. 템플릿에 플레이스홀더가 **하나도 없으면** 인자를 조용히 버리지 않고 뒤에 붙여줍니다. [관찰]

```js
if (!c && n && t) e = e + `\nARGUMENTS: ${s(t)}`;
```

> **보안 주의.** `` !`명령` `` 블록 안에 `$ARGUMENTS` 를 넣지 마세요. **인자는 셸 이스케이프되지 않습니다.** 사용자가 친 문자열이 그대로 셸에 들어가므로 커맨드 인젝션이 됩니다. Claude Code 자신의 임포터도 이 점을 경고합니다. [관찰]

## 그리고 여기서 훅이 끼어든다

입력이 메시지가 된 직후, API 요청이 조립되기 전에 **`UserPromptSubmit` 훅**이 실행됩니다. 훅의 표준출력은 `<system-reminder>` 블록이 되어 그대로 모델의 컨텍스트로 들어갑니다. [관찰]

즉 **여러분이 치지 않은 텍스트를 대화에 끼워 넣을 수 있는 자리**가 여기입니다. 6편에서 자세히 다룹니다.

## 마지막으로 — 트랜스크립트 ≠ API 요청

0편에서 레코드 종류를 세어봤을 때 `attachment` 가 159 건으로 가장 많았던 걸 기억하시나요? 이제 이유를 알 수 있습니다.

**트랜스크립트는 "이 세션에서 일어난 모든 일"의 기록이고, API 요청은 그중 일부만 담습니다.**

- `type:"system"` + `subtype:"local_command"` → API 로 안 감
- `attachment`, `file-history-snapshot`, `last-prompt`, `mode` → 전부 로컬 살림살이
- `user`, `assistant` → 이것이 실제 대화

> 그래서 "트랜스크립트에 있으니 모델도 봤겠지"라고 넘겨짚으면 안 됩니다. 모델이 실제로 무엇을 봤는지 확인하는 유일한 방법은 **요청 바디를 직접 캡처하는 것**입니다. 0편에서 세팅한 로컬 싱크가 그래서 필요합니다.

## 정리

- 입력의 **첫 글자**가 경로를 정합니다. 다섯 갈래가 서로 다른 코드로 갑니다.
- **대부분의 슬래시 커맨드는 모델을 부르지 않습니다.** 221 건의 로컬 커맨드 출력 중 모델 호출이 뒤따른 건 실질적으로 0 건이었습니다.
- `!` 는 셸에서 실행되고 결과가 대화 기록에 남지만, 보통 모델을 부르진 않습니다.
- **`@파일` 은 툴 호출이 아닙니다.** 하네스가 미리 읽어서 "읽은 것처럼" 텍스트를 심습니다.
- 커스텀 커맨드에서 **`$1` 은 두 번째 인자**입니다. 첫 번째는 `$0`.
- 트랜스크립트에 있는 것이 전부 API 로 가는 건 아닙니다.

## 확인 못 한 것

1. 로컬 슬래시 커맨드가 `type:"user"` 로 기록될 때와 `type:"system"` 으로 기록될 때의 **선택 기준**. 같은 커맨드가 양쪽으로 나타나고 버전과도 무관했습니다.
2. `#` 접두사의 **실제 동작**. 바이너리에 태그 문자열이 있는 것만 확인했고, 제 트랜스크립트에는 진짜 사용 기록이 없었습니다.
3. 커스텀 커맨드는 **인터랙티브 TUI 없이** 관찰한 것이라, REPL 에서 직접 칠 때 다른 경로를 타는지는 확인하지 못했습니다.

다음 편에서는 이렇게 만들어진 메시지 배열이 **실제 HTTP 요청으로 조립되는 과정**을 봅니다. 시스템 프롬프트는 몇 조각인지, `CLAUDE.md` 는 정확히 어디에 들어가는지 — 대부분의 사람이 틀리게 알고 있는 지점입니다.

> 이전 편: [0편. 프롤로그 — Claude Code는 결국 while 루프 하나다](./00-prologue.md)
> 다음 편: [2편. 요청 바디 해부 — LLM에게 실제로 보내는 것](./02-request-body.md)
