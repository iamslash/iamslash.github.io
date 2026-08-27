# 부록. `~/.claude` 안내 지도

> 시리즈: Claude Code 내부 구조 (builtin 기준, v2.1.243)
> 이 편에서 배우는 것: `~/.claude` 안의 항목들이 각각 무엇인지, **왜 이렇게 많은지**, `settings.json` 과 `.claude.json` 의 차이, 그리고 무엇을 지워도 되는지.

시리즈 내내 이런 경로들이 나왔습니다.

```
~/.claude/projects/          트랜스크립트          (0편~)
~/.claude/agents/            에이전트 정의          (8편)
~/.claude/settings.json      권한과 훅              (5·6편)
~/.claude/shell-snapshots/   ???                    (아직 안 나옴)
```

이제 전체 지도를 그립니다. 먼저 열어봅시다.

```bash
ls -A ~/.claude | wc -l
du -sh ~/.claude
```

제 머신에서는 **40 개 항목, 2.0GB** 였습니다. [관찰] (쓸수록 늘어나니 여러분 숫자는 다릅니다.)

처음 보면 압도적입니다. 그런데 여기엔 좋은 소식이 있습니다.

## 반전 — 깨끗하게 실행하면 네 개만 생긴다

0편에서 쓴 로컬 싱크와 `CLAUDE_CONFIG_DIR` 을 다시 씁니다. **완전히 빈 설정 디렉터리**로 한 번만 실행해서, Claude Code 가 **처음부터 만드는 것**이 무엇인지 봅시다.

```bash
S=/tmp/ccdir-lab; mkdir -p $S/lab && cd $S/lab
git init -q . && echo hi > a.txt && git add -A \
  && git -c user.email=a@b -c user.name=t commit -qm init

# 0편의 sink.py 를 띄워둔 상태에서 (포트 8931)
CLAUDE_CONFIG_DIR=$S/cfg ANTHROPIC_BASE_URL=http://127.0.0.1:8931 \
  ANTHROPIC_API_KEY=sk-ant-fake \
  claude -p "Reply with exactly: PONG" --model claude-haiku-4-5-20251001

find $S/cfg -maxdepth 2 | sort
```

결과입니다. [관찰]

```
cfg
cfg/.claude.json
cfg/backups
cfg/backups/.claude.json.backup.1787755114861
cfg/projects
cfg/projects/-private-tmp-ccdir-lab-lab
cfg/sessions
```

**네 개뿐입니다.**

> **단, 요청이 성공했을 때 얘기입니다.** 싱크를 안 띄운 채로 돌리면 연결이 거부되면서 `.last-cleanup` 이 하나 더 생겨 **다섯 개**가 됩니다. 숫자가 안 맞으면 이걸 먼저 의심하세요. [관찰]

> **`~/.claude` 는 설정 폴더라기보다 내가 Claude Code 로 무엇을 해왔는지의 기록에 가깝습니다.**

무엇이 언제 생기는지 몇 가지만 짚으면 이렇습니다.

| 언제 생기나 | 예 |
|---|---|
| 첫 실행이면 무조건 | `.claude.json` · `backups/` · `projects/` · `sessions/` |
| 대화형으로 한 번만 써도 | `shell-snapshots/`, `history.jsonl` |
| 파일을 고치면 | `file-history/` (되돌리기를 쓰든 안 쓰든) |
| 서브에이전트를 쓰면 | `projects/<slug>/<session-id>/subagents/` |
| 내가 직접 만들어야 | `agents/`, `skills/`, `commands/`, `CLAUDE.md` |
| 알아서 쌓이는 살림살이 | `cache/`, `telemetry/`, `stats-cache.json`, `.last-cleanup` |

> **주의 — 위 실험이 증명하는 것과 아닌 것.** 이 실험이 보여준 건 **"이 넷이 최소 베이스라인"** 이라는 것뿐입니다. 나머지가 전부 "내가 기능을 골라 써서" 생겼다는 뜻은 **아닙니다.** [추론] 표의 아래 두 줄처럼, 그냥 쓰기만 해도 자동으로 생기는 것이 상당수입니다. `-p` 한 번은 대화형 기능도, 파일 편집도, 백그라운드 작업도 건드리지 않으니까요.

이 관점으로 보면 지도가 훨씬 읽기 쉬워집니다. 카테고리별로 봅시다.

## 1. 대화가 쌓이는 곳 — 압도적으로 큰 두 개

### `projects/` — 1.8GB

0편부터 계속 써온 트랜스크립트입니다. 프로젝트 경로의 `/` 를 `-` 로 바꾼 디렉터리 안에 세션별 JSONL 이 들어 있습니다.

```bash
du -sh ~/.claude/projects/* | sort -rh | head -5
```

제 경우 한 프로젝트가 **1.6GB** 를 혼자 차지했습니다. [관찰] 안에 있는 파일 유형을 세어보면 시리즈에서 본 것들이 그대로 나옵니다.

```bash
find ~/.claude/projects -type f | sed 's|.*\.||' | sort | uniq -c | sort -rn | head
```

```
 943 jsonl    ← 트랜스크립트 (메인 + 서브에이전트 + 워크플로)
 843 json     ← .meta.json 등
 169 md
 103 txt      ← tool-results/ 스필 (4편)
```

세션 하나의 전체 구조는 7편에서 본 것에 워크플로 산출물(9편)까지 더하면 이렇습니다.

```
projects/<slug>/
├── <session-id>.jsonl              메인 트랜스크립트
└── <session-id>/
    ├── subagents/                  서브에이전트별 JSONL + meta.json  (7편)
    │   └── workflows/<runId>/      워크플로 실행 + journal.jsonl     (9편)
    ├── tool-results/               100,000자 넘는 툴 결과 스필       (4편)
    └── memory/
```

### `history.jsonl` — 내가 친 모든 프롬프트

```bash
wc -l < ~/.claude/history.jsonl
head -1 ~/.claude/history.jsonl | python3 -m json.tool
```

```json
{
  "display": "exit",
  "pastedContents": {},
  "timestamp": 1775855061302,
  "project": "/Users/iamslash/prj/github",
  "sessionId": "9e5f2fea-484c-4724-9fd5-7902c801897b"
}
```

제 머신에 **14,631 줄** 이 쌓여 있었습니다. [관찰] 터미널에서 위쪽 화살표로 이전 프롬프트를 불러오는 그 기록입니다.

민감한 건 `display` 만이 아닙니다. **붙여넣은 내용은 `pastedContents` 에 통째로** 들어갑니다. 위 샘플은 비어 있어서 무해해 보이지만, 세어보면 다릅니다. [관찰]

```bash
python3 -c "
import json,os
rows=[json.loads(l) for l in open(os.path.expanduser('~/.claude/history.jsonl')) if l.strip()]
n=sum(1 for r in rows if r.get('pastedContents'))
print(f'전체 {len(rows)}건 중 붙여넣기 포함 {n}건')"
```

> **비밀번호나 토큰을 프롬프트에 치거나 붙여넣은 적이 있다면 여기 남아 있습니다.** 같은 내용이 `paste-cache/` 에도 별도 파일로 남습니다.

## 2. 되돌리기의 재료 — `file-history/`

두 번째로 큰 항목입니다. 제 경우 **117MB, 5,865 개 파일**. [관찰]

```bash
ls ~/.claude/file-history | head -3
find ~/.claude/file-history -type f | head -2
```

세션 UUID 별 디렉터리 안에 `<해시>@v1`, `<해시>@v2` 같은 이름의 파일이 들어 있고, **내용은 그 시점의 파일 원본 전체**입니다.

1편에서 트랜스크립트 레코드 타입을 셀 때 `file-history-snapshot` 이 나왔던 것 기억하시나요? 그게 여기를 가리킵니다. **Claude Code 가 파일을 고치기 전에 사본을 떠두기 때문에** 되돌리기가 가능합니다.

> 용량이 부담되면 여기가 첫 번째 후보입니다. 다만 **지우면 그만큼 과거 시점으로 되돌릴 수 없게 됩니다.**

## 3. 내가 만드는 것들

여기가 여러분이 실제로 편집하는 영역입니다.

| 경로 | 무엇 | 다룬 편 |
|---|---|---|
| `settings.json` | 권한 규칙, 훅 | 5·6편 |
| `CLAUDE.md` | 전역 메모리 | 2편 |
| `agents/*.md` | 커스텀 서브에이전트 | 8편 |
| `skills/` | 커스텀 스킬 | 9편 |
| `commands/` | 커스텀 슬래시 커맨드 | 1편 — **만들어야 생깁니다.** 제 머신엔 없습니다 |
| `plugins/` | 설치한 플러그인 | — |

제 `settings.json` 은 **1.8KB** 인데 `plugins/` 는 **108MB, 10,810 개 파일** 이었습니다. [관찰] 플러그인은 생각보다 무겁습니다.

## 4. ⚠️ `settings.json` vs `.claude.json` — 가장 헷갈리는 지점

**둘은 완전히 다른 파일이고, 위치도 다릅니다.**

```bash
ls -la ~/.claude/settings.json     # 내가 편집하는 설정
ls -la ~/.claude.json              # ← 주의: .claude/ 안이 아니라 홈 디렉터리 바로 아래
```

> 앞의 실험에서는 `cfg/.claude.json` 처럼 **설정 디렉터리 안**에 생겼는데 왜 다를까요? `CLAUDE_CONFIG_DIR` 을 지정하면 이 파일도 **그 디렉터리 안으로 따라 들어가기** 때문입니다. 지정하지 않은 평소에는 홈 디렉터리 바로 아래에 놓입니다. 그래서 앞의 베이스라인 네 개 중 `.claude.json` 은 **평소엔 `~/.claude/` 밖에 있습니다.**

| | `~/.claude/settings.json` | `~/.claude.json` |
|---|---|---|
| 위치 | `.claude/` **안** | 홈 디렉터리 **바로 아래** |
| 크기(제 경우) | 1.8KB | **108KB** |
| 누가 쓰나 | **내가** 편집 | **Claude Code 가** 관리 |
| 내용 | 권한·훅·환경변수 | 상태·캐시·기능 플래그, **MCP 서버 설정**, 프로젝트별 신뢰 상태 |
| 손으로 고쳐도 되나 | 예 | **직접 편집하지 마세요** — CLI 로 바꾸세요 |

> `.claude.json` 이 순수한 캐시는 아닙니다. `claude mcp add -s user` 로 등록한 MCP 서버가 여기 저장되고, `projects` 항목에는 프로젝트별 `allowedTools` 와 신뢰 수락 여부가 들어 있습니다. **다만 손으로 고치지 말고 CLI 를 쓰세요** — 형식이 바뀌면 조용히 무시됩니다.

`.claude.json` 의 최상위 키가 **79 개** 입니다. [관찰]

```bash
python3 -c "
import json,os
d=json.load(open(os.path.expanduser('~/.claude.json')))
print(len(d),'keys'); print(sorted(d)[:20])"
```

여기서 5편과 8편에서 "게이트가 서버 사이드라 알 수 없다"고 반복했던 그 기능 플래그들을 **열거할 수 있습니다.**

```bash
python3 -c "
import json,os
gb=json.load(open(os.path.expanduser('~/.claude.json'))).get('cachedGrowthBookFeatures') or {}
print('플래그', len(gb), '개')
print('trellis 있나?:', 'tengu_hazel_trellis' in gb)
print([k for k in sorted(gb) if 'hazel' in k][:5])"
```

```
플래그 550 개
trellis 있나?: True
['tengu_cobalt_plinth_hazel', 'tengu_hazel_osprey', 'tengu_hazel_osprey_floor', 'tengu_hazel_trellis']
```

**550 개**가 나왔고, 4편에서 다룬 **서브에이전트 중첩 깊이(기본 3)를 제어하는** 플래그 `tengu_hazel_trellis` 도 그 안에 있었습니다(값도 `3` 입니다). [관찰]

> **다만 이게 모든 걸 풀어주진 않습니다.** 캐시는 **플래그 이름과 값의 목록**일 뿐이고, 5편의 `ou()` 나 8편의 `G6()` 같은 난독화된 게이트 함수가 **어느 플래그를 읽는지는 여전히 알 수 없습니다.** "어떤 실험이 켜져 있나"는 답할 수 있고, "이 분기를 켜는 게 무엇인가"는 못 답합니다.
>
> 캐시에 없는 이름은 기본값으로 동작할 가능성이 높지만, 캐시가 오래됐거나 이 계정에 안 내려온 것일 수도 있습니다. [추론]

## 5. 실행 환경 — 바이너리 분석을 조용히 망치는 함정

### `shell-snapshots/`

시리즈에서 한 번도 설명하지 않고 지나친 디렉터리인데, **바이너리를 분석할 때 사람을 조용히 속이는 범인**이 여기 있습니다.

```bash
ls -la ~/.claude/shell-snapshots/
head -5 ~/.claude/shell-snapshots/$(ls ~/.claude/shell-snapshots | head -1)
```

```
# Snapshot file
# Unset all aliases to avoid conflicts with functions
unalias -a 2>/dev/null || true
# Functions
VCS_INFO_formats () {
```

**여러분의 zsh 함수와 별칭을 통째로 덤프한 파일**입니다. 제 것은 하나에 94KB 였습니다. [관찰]

Claude Code 는 `Bash` 툴을 실행할 때 이 스냅샷을 먼저 읽어들입니다. 그래야 **대화형 셸에서 치던 것과 같은 환경**이 되니까요.

편리하지만 대가가 있습니다. 직접 확인해보세요. [관찰]

```bash
grep -c 'ugrep' ~/.claude/shell-snapshots/$(ls -t ~/.claude/shell-snapshots | head -1)
```

제 머신에서는 **4** 가 나왔습니다. 그런데 제가 `ugrep` 을 쓰도록 설정한 적은 없습니다. 스냅샷 안을 보면 범인이 나옵니다. [관찰]

```bash
SNAP=~/.claude/shell-snapshots/$(ls -t ~/.claude/shell-snapshots | head -1)
/usr/bin/grep -n "^alias -- grep=" "$SNAP"
/usr/bin/grep -n "Shadow find/grep\|unalias grep\|ARGV0=ugrep" "$SNAP"
```

```
2984:alias -- grep='grep --color=auto --exclude-dir={.bzr,CVS,.git,...}'
3067:# Shadow find/grep with embedded bfs/ugrep
3069:unalias grep 2>/dev/null || true
3091:    ARGV0=ugrep "$_cc_bin" -G --ignore-files --hidden -I --exclude-dir=.git ...
3093:    ARGV0=ugrep "$_cc_bin" -G --ignore-files --hidden -I --exclude-dir=.git ...
```

(줄 번호는 여러분 스냅샷에 따라 다릅니다. `ARGV0=ugrep` 이 두 번 나오는 건 인자 유무에 따라 분기하기 때문입니다.)

**순서를 보세요.**

1. 2984 줄 — 제 진짜 alias 는 그냥 `grep --color=auto` 입니다. `ugrep` 과 무관합니다.
2. 3069 줄 — 스냅샷 **끝에서 Claude Code 가 그 alias 를 지웁니다.**
3. 3091 줄 — 그리고 **자기 함수를 심습니다.** 내장 바이너리를 `ugrep` 으로 실행하는 함수입니다.

즉 **제 설정이 새어 나간 게 아니라, Claude Code 가 의도적으로 `grep` 을 갈아끼운 것**입니다. `find` 도 같은 방식으로 `bfs` 로 바뀝니다.

런타임에서 확인할 수 있습니다.

```bash
type grep
# grep is a shell function from /Users/iamslash/.claude/shell-snapshots/snapshot-zsh-....sh
```

> **왜 이렇게 할까요?** `ugrep`/`bfs` 는 `.gitignore` 를 존중하고 숨김 파일을 다루는 규칙이 다릅니다. 코드베이스를 뒤지는 데는 이쪽이 낫습니다. [추론]
>
> **하지만 이 시리즈를 재현할 때는 문제가 됩니다.** 361MB 짜리 바이너리에 복잡한 정규식을 걸면 GNU `grep` 과 **다른 결과나 다른 에러**가 나올 수 있습니다. 그래서 이 시리즈의 바이너리 분석 명령은 `/usr/bin/grep` 처럼 **절대경로**를 씁니다. (어떤 정규식에서 정확히 갈리는지는 재현해보지 않았습니다. [추론])

### `session-env/`, `sessions/`, `jobs/`

- `session-env/` — 세션별 환경 (제 경우 98 개 파일)
- `jobs/` — 백그라운드 작업 (제 경우 69 개 파일)
- `sessions/` — **지금 돌고 있는 Claude Code 프로세스들의 명부**입니다

`sessions/` 를 열어보면 이 시리즈에서 아직 안 다룬 기능이 드러납니다. [관찰]

```bash
cd ~/.claude/sessions && python3 -c "
import json,glob
d=json.load(open(sorted(glob.glob('*.json'))[0]))
print(sorted(d))
print('socket:', d.get('messagingSocketPath'))"
ls ~/.claude/sessions/*.key | head -2
```

```
['bridgeSessionId', 'cwd', 'entrypoint', 'kind', 'messagingSocketPath', 'name',
 'nameSince', 'nameSource', 'peerFeatures', 'peerProtocol', 'pid', 'procStart',
 'sessionId', 'startedAt', 'status', 'statusUpdatedAt', 'updatedAt', 'version']
socket: /tmp/cc-socks/26316.sock
```

> **키 목록은 세션 상태에 따라 달라집니다.** 이 파일은 죽은 기록이 아니라 **살아 있는 프로세스의 현재 상태**입니다. 실제로 위 명령을 조금 뒤에 다시 돌렸더니 `waitingFor` 가 하나 더 붙어 있었습니다 — 그 세션이 무언가를 기다리는 중이었기 때문입니다. [관찰]

`<pid>.json` 은 그 프로세스의 명찰이고, 짝으로 있는 `<pid>.<64자리 해시>.key` 와 유닉스 소켓이 **세션끼리 메시지를 주고받는 통로**입니다. 여러 Claude Code 를 동시에 띄워본 적이 있다면 여기에 흔적이 남습니다. (이 주제는 시즌 2 에서 다룹니다.)

## 6. 멀티에이전트가 남기는 것

7편과 8편에서 본 것들이 디스크에 이렇게 남습니다.

| 경로 | 무엇 |
|---|---|
| `teams/session-<id>/` | 팀 단위 실행 상태 |
| `tasks/session-<id>/` | 세션별 태스크 (제 경우 42 개 세션분) |
| `agent-memory/<agentType>/` | 에이전트 전용 메모리 (8편의 `memory:` frontmatter) [추론] |

`tasks/` 아래 디렉터리 개수를 세보면 **내가 백그라운드 작업을 얼마나 썼는지**가 그대로 나옵니다.

```bash
ls ~/.claude/tasks | wc -l
ls ~/.claude/teams | wc -l
```

## 7. 민감한 것 — `secrets/`

```bash
ls -la ~/.claude/secrets/
```

```
-rw-------  148  discord-hn-digest.env
-rw-------  860  judging-api-keys.env
-rw-------  146  metabase-local.env
...                                      (8개 중 3개만 표시)
```

**퍼미션이 `600`** 입니다. 실제 API 키가 들어 있는 `.env` 파일들입니다.

> **`~/.claude` 를 통째로 백업하거나 공유하기 전에 읽으세요.** 민감한 것은 `secrets/` 만이 아닙니다.
>
> | 경로 | 무엇이 들어 있나 |
> |---|---|
> | `secrets/` | API 키 원본 (`600`) |
> | `history.jsonl` | 내가 친 모든 프롬프트(`display`)와 **붙여넣은 내용**(`pastedContents`) |
> | `projects/` | 트랜스크립트 — Claude 가 읽은 **파일 내용 전체**, 명령 출력, 거기 섞인 환경변수까지 |
> | `file-history/` | 편집 **전** 파일 원본 사본. `.env` 를 고친 적이 있다면 그 값도 |
> | `paste-cache/` | 붙여넣은 원문이 별도 파일로 |
> | `~/.claude.json` | 계정 식별자와 MCP 서버 설정 (퍼미션 `600`) |
>
> 용량으로 보면 뒤의 둘이 훨씬 크고, 민감도도 결코 낮지 않습니다. **`~/.claude` 는 통째로 공유해도 되는 디렉터리가 아닙니다.**

## 8. 내 것이 아닌 것 가려내기

8편에서 배운 **대조군 방법**을 여기에도 씁니다. 항목 이름이 Claude Code 바이너리에 존재하는지 보면 됩니다.

**단, 이름이 짧으면 그냥 검색하면 안 됩니다.** 따옴표를 씌우거나 경로 형태로 좁혀야 합니다. 그리고 **있어야 할 것(양성 대조군)** 을 같이 돌려야 결과를 믿을 수 있습니다.

```bash
B=~/.local/share/claude/versions/2.1.243
printf '%-22s %8s %8s\n' '항목' '"name"' '/name'
for f in shell-snapshots file-history agent-memory hud ZZQuuxNotAThing; do
  q=$(LC_ALL=C grep -ac -- "\"$f\"" "$B"); p=$(LC_ALL=C grep -ac -- "/$f" "$B")
  printf '%-22s %8s %8s\n' "$f" "${q:-0}" "${p:-0}"
done
```

```
항목                       "name"    /name
shell-snapshots               6        0
file-history                  6        0
agent-memory                  2        7
hud                           0        0
ZZQuuxNotAThing               0        0
```

위 셋은 **양성 대조군**입니다. 이들이 0 이 아니라는 것이 "이 검색이 작동한다"는 증거이고, 그래야 `hud` 의 0 이 의미를 갖습니다. 맨 아래 `ZZQuuxNotAThing` 은 음성 대조군입니다.

고유한 파일명은 좁힐 필요 없이 그대로 검색해도 됩니다.

```bash
for f in .omc-config.json codex-watchdog.sh .session-stats.json; do
  printf '%-24s %s\n' "$f" "$(LC_ALL=C grep -acF -- "$f" "$B")"
done
# 전부 0
```

제 머신에서 **builtin 이 아닌 것**은 이렇게 가려졌습니다. [관찰]

```
hud/  .omc/  .omc-config.json  .omc-version.json
codex-watchdog.sh  .session-stats.json  settings.json.bak
```

전부 제가 설치한 플러그인이 만든 것이거나(oh-my-claudecode, codex), 제가 손으로 만든 백업입니다.

> **제가 실제로 밟은 함정입니다.** 처음엔 좁히지 않고 `ide` 로 검색했더니 **9,313 건**이 나왔습니다. 전부 `provide`·`video` 같은 단어 안의 `ide` 였죠. `hud` 도 좁히지 않으면 **16** 이 나와서 "builtin 이네" 하고 넘어갈 뻔했습니다. 9편에서 `SlashCommand` 를 두고 똑같은 함정을 만났었습니다 — **부분 문자열과 진짜 이름은 다릅니다.**
>
> 참고로 `grep -c` 는 **매칭된 줄 수**를 셉니다. 한 줄에 여러 번 나와도 1 입니다. 여기서는 "있나 없나"만 보면 되므로 상관없습니다.

## 9. 무엇을 지워도 되나

용량 순으로 정리하면 이렇습니다.

| 경로 | 크기(제 경우) | 지워도 되나 |
|---|---|---|
| `projects/` | 1.8GB | **주의.** 지우면 `/resume` 과 과거 대화가 사라집니다 |
| `file-history/` | 117MB | 대체로 안전. 되돌리기 범위만 줄어듭니다 |
| `plugins/` | 108MB | **부분적으로만.** `marketplaces/`·`cache/` 는 재설치되지만, `installed_plugins.json` 을 같이 지우면 **무엇을 설치했는지 기록이 사라집니다** |
| `paste-cache/` | 208KB | 안전(내용이 `history.jsonl` 에 중복). 단 **민감** |
| `image-cache/` | 1.1MB | 세션 첨부 이미지. 지우면 해당 트랜스크립트의 그림이 사라집니다 |
| `shell-snapshots/` | 384KB | 안전. 다음 실행에 다시 생깁니다 |
| `secrets/` | 32KB | **절대 안 됨** |
| `cache/`, `telemetry/`, `stats-cache.json`, `*-cache.json` | 작음 | 안전. 알아서 다시 생깁니다 |
| `settings.json`, `CLAUDE.md`, `agents/`, `skills/` | 작음 | **절대 안 됨** — 여러분이 만든 것 |

> **지우기 전에 Claude Code 를 전부 종료하세요.** `shell-snapshots/`, `sessions/`, `tasks/` 는 **돌고 있는 세션이 지금 쓰고 있는** 파일입니다. 실행 중에 지우면 그 세션의 `Bash` 툴이나 세션 간 메시징이 깨질 수 있습니다.

오래된 프로젝트만 골라 지우고 싶다면:

```bash
du -sh ~/.claude/projects/* | sort -rh | head -10
```

큰 것부터 보고 필요 없는 프로젝트 디렉터리만 지우면 됩니다.

> **지우기 전에 한 번만 확인하세요.** 이 시리즈의 모든 검증 명령이 `projects/` 를 읽습니다. 이걸 비우면 여러분 머신에서 재현할 데이터도 같이 사라집니다.

## 정리

- 빈 설정으로 한 번 실행하면 **`.claude.json` · `backups/` · `projects/` · `sessions/`** 네 개만 생깁니다. 나머지는 **내가 이 도구를 써온 기록**입니다 — 기능을 골라 켠 것도, 그냥 쓰다 보니 쌓인 것도 섞여 있습니다.
- 용량은 사실상 **`projects/`(트랜스크립트)와 `file-history/`(파일 스냅샷)** 둘이 전부입니다.
- **`~/.claude/settings.json` 과 `~/.claude.json` 은 다른 파일**입니다. 후자는 홈 디렉터리 바로 아래에 있고, **Claude Code 가 관리하므로 손대지 마세요.**
- 그 `~/.claude.json` 안에 **기능 플래그 캐시(550 개)** 가 있습니다. 시리즈 내내 "알 수 없다"고 했던 플래그들을 **열거**할 수 있습니다. 다만 어느 게이트가 어느 플래그를 읽는지까지는 여전히 알 수 없습니다.
- **`shell-snapshots/`** 때문에 여러분의 셸 별칭·함수가 `Bash` 툴까지 따라갑니다. 바이너리를 뒤질 땐 `/usr/bin/grep` 처럼 절대경로를 쓰세요.
- **`secrets/` 와 `history.jsonl`** 은 민감합니다. 백업·공유 전에 반드시 확인하세요.
- 내 것이 아닌 항목은 **대조군을 낀 바이너리 검색**으로 가려낼 수 있습니다. 단 **고유한 이름에만** 쓰세요.

## 확인 못 한 것

1. **어느 항목이 정확히 언제 생기는지**를 항목별로 검증하지는 않았습니다. 위 "언제 생기나" 표는 `-p` 한 번의 베이스라인 실험과 각 디렉터리의 내용에서 **역추론한 것**이라, 기능별로 하나씩 켜보며 확인한 결과가 아닙니다. [추론]
2. `ide/`, `downloads/` 는 비어 있어서 실제로 무엇이 들어가는지 확인하지 못했습니다.
3. `.last-cleanup`, `.last-update-result.json` 은 이름과 바이너리 매칭으로만 판단했고 내용을 검증하지 않았습니다.

> 이전 편: [9편. Workflow와 확장 표면](./09-workflow-and-skills.md)
> 시리즈 처음: [0편. 프롤로그 — Claude Code는 결국 while 루프 하나다](./00-prologue.md)
