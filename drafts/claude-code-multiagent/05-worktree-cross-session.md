# 5편. worktree 격리와 교차 세션 메시징

> 시리즈: Claude Code 멀티에이전트 (builtin 기준)
> 이 편에서 배우는 것: 에이전트 여럿이 **파일을 고칠 때** 생기는 문제, git worktree 격리가 그걸 어떻게 푸는지, **변경이 자동으로 돌아오지 않는다는 것**, 그리고 세션끼리 메시지를 주고받는 구조.

지금까지 네 편은 대체로 **읽는** 작업이었습니다. 탐색하고, 검토하고, 보고서를 씁니다.

이제 **쓰기 시작하면** 새로운 문제가 생깁니다.

## 문제 — 다섯이 같은 파일을 고치면

에이전트 다섯에게 각각 다른 버그를 고치라고 시켰다고 해봅시다. 전부 같은 저장소, 같은 워킹 트리에서 돕니다.

```
agent-1: src/auth.py 를 읽고 → 고친다
agent-2: 같은 파일을 읽고 → 고친다      ← agent-1 이 고치기 전 내용을 읽었다면?
agent-3: git checkout 다른브랜치         ← 나머지 넷의 발밑이 사라진다
```

시즌 1 의 5편에서 본 파일 상태 추적(`File has been modified since read`)이 **한 에이전트 안에서는** 이걸 막아줍니다. 하지만 에이전트가 여럿이면 서로의 변경을 밟습니다. 브랜치를 바꾸는 순간은 더 심각하고요.

## `isolation: "worktree"`

해법은 오래된 git 기능입니다. **에이전트마다 자기 워킹 트리를 줍니다.**

```yaml
---
name: fix-bug
isolation: worktree
---
```

또는 `Agent` 툴 호출에 `isolation: "worktree"` 를 넘깁니다.

### 어디에 생기나

에이전트 안에서 `pwd` 를 찍어보면 이렇습니다. [관찰]

```
.../lab2/.claude/worktrees/agent-a4d546d925b40a54b     ← cwd 가 worktree
```

브랜치도 전용으로 하나 생깁니다.

```bash
git rev-parse --abbrev-ref HEAD
# worktree-agent-a4d546d925b40a54b

git worktree list
# .../lab2                                            3c54e5c [main]
# .../lab2/.claude/worktrees/agent-a4d546d..  3c54e5c [worktree-agent-a4d546d...] locked
```

**`locked` 가 붙어 있습니다.** 도는 동안 다른 프로세스가 함부로 지우지 못하게 잠급니다. [관찰]

### 특별한 마법이 아닙니다

`.git` 을 열어보면 확인됩니다.

```bash
W=<repo>/.claude/worktrees/agent-<id>
cat $W/.git
# gitdir: .../lab2/.git/worktrees/agent-a4d546d925b40a54b
```

**163 바이트짜리 포인터 파일**입니다. 평범한 `git worktree add` 와 **완전히 같은 구조**입니다. [관찰] Claude Code 만의 메커니즘이 아니라 git 기능을 그대로 씁니다.

격리도 확인됩니다.

```bash
ls <repo>/probe-artifact.txt        # No such file or directory  ← 메인 트리엔 없다
git -C $W status --porcelain        # ?? probe-artifact.txt      ← worktree 안에만 있다
```

## 반전 — 변경은 자동으로 돌아오지 않는다

여기가 가장 오해하기 쉬운 지점입니다.

에이전트가 worktree 안에서 파일을 고쳤습니다. 그럼 끝나고 나면 메인 트리에 반영될까요?

**아닙니다.** [관찰]

- 파일은 worktree 안에 **커밋도 안 된 untracked 상태**로 남습니다
- 메인 트리에는 **나타나지 않습니다**
- 머지도, 체리픽도, 복사도 **자동으로는 일어나지 않습니다**

호출자에게 돌아오는 건 **경로와 브랜치 이름뿐**입니다.

```json
{"worktreePath": ".../\.claude/worktrees/agent-a4d546d925b40a54b",
 "worktreeBranch": "worktree-agent-a4d546d925b40a54b"}
```

> **그래서 `isolation: worktree` 는 "격리해서 안전하게 고쳐줘"가 아니라 "격리해서 고친 결과를 저기 둬줘"입니다.** 가져오는 건 여러분(또는 부모 에이전트) 몫입니다. 브리핑에 **"작업이 끝나면 커밋하고 브랜치 이름을 보고하라"** 를 넣어두면 편합니다. 1편에서 말한 "답의 형태를 명시하라"가 여기서도 그대로 적용됩니다.

worktree 를 직접 드나드는 전용 툴도 따로 있습니다 — `EnterWorktree` / `ExitWorktree`. 후자는 이렇게 안내합니다. [문서]

```
"keep" leaves the worktree and branch on disk; "remove" deletes both.
Required true when action is "remove" and the worktree has uncommitted files
or unmerged commits. The tool will refuse and list them otherwise.
```

**커밋 안 된 게 있으면 지우기를 거부**하고 목록을 보여줍니다.

## 아무것도 안 바꿨으면 알아서 지웁니다

에이전트가 파일을 하나도 안 건드렸다면 worktree 를 남길 이유가 없죠. 자동으로 정리됩니다.

판별은 `.meta.json` 으로 합니다. 두 경우를 나란히 놓으면 명확합니다. [관찰]

```json
// 변경 있음 → 보존
{"agentType":"wt-probe", "worktreePath":"...", "spawnedWithWorktree":true,
 "worktreeBranch":"worktree-agent-...", "spawnDepth":1}

// 변경 없음 → 자동 삭제
{"agentType":"wt-noop", "spawnDepth":1,
 "worktreeCleanlyRemoved":true}          ← 이 키 하나로 판별됩니다
```

`worktreePath` / `worktreeBranch` / `spawnedWithWorktree` 가 **전부 사라지고** `worktreeCleanlyRemoved: true` 만 남습니다.

번들 코드도 그대로 보입니다. [관찰] (이 부분은 **2.1.246** 에서 뽑았습니다 — 0편의 "코드 인용은 2.1.243" 규칙의 예외입니다. 2.1.243 에는 이 함수가 같은 이름으로 없습니다.)

```js
if (Nt) {
  if (!await KGe(Ye, Nt) && (await H7(Ye, gt, jt, !1, "agent_tool")).outcome === "removed")
    return ber({ ... }), {};        // ← 빈 객체! 경로를 안 돌려준다
}
return b(`Agent worktree kept at: ${Ye}`), { worktreePath: Ye, worktreeBranch: gt };
```

`KGe(경로, headCommit)` 가 "변경됐나?" 판정이고, 변경이 없으면 제거한 뒤 **`{}`** 를 반환합니다. 즉 **`worktreePath` 가 안 돌아왔다면 자동 삭제된 것**입니다.

브랜치도 같이 지워집니다. 다만 주의할 게 있습니다.

> **손으로 `git worktree remove` 하면 브랜치가 남습니다.** 자동 삭제만 브랜치까지 정리합니다. [관찰] 실험을 반복하다 보면 `worktree-agent-*` 브랜치가 쌓이니 가끔 `git branch -a` 로 확인하세요.

### 자동 삭제되지 않는 예외 셋 [관찰]

1. **훅 기반 worktree** — `Hook-based agent worktree kept at:`
2. **부모가 백그라운드 대기 중일 때** — `backgrounded owner awaits keepalive, resume pending`
3. **파일이 하나라도 바뀐 경우** — **untracked 파일 포함**

3 번이 함정입니다. 조사할 때 실제로 걸렸습니다 — 플러그인 훅이 worktree 안에 상태 파일을 하나 써버려서, 아무것도 안 한 에이전트인데도 worktree 가 남았습니다. **여러분 훅이나 도구가 부산물을 남기면 자동 정리가 안 됩니다.** `.gitignore` 에 넣으면 해결됩니다.

### 비용

순수 git 연산만 재면 **생성·삭제 각각 40ms 안팎**입니다(커밋 2 개짜리 초소형 저장소, n=3). [관찰]

```
add=0.042s remove=0.036s
add=0.036s remove=0.035s
add=0.036s remove=0.034s
```

> 다만 **체크아웃 비용은 트리 크기에 비례**합니다. 파일 두 개짜리 저장소라서 40ms 인 것이고, 실제 저장소에서는 훨씬 큽니다. [추론] 에이전트 스무 개에 전부 worktree 를 주기 전에 한 번 재보세요.

## 교차 세션 메시징

여기서 축이 바뀝니다. 지금까지는 **한 세션 안의** 부모-자식이었습니다. 이제 **서로 다른 Claude Code 프로세스** 이야기입니다.

0편에서 새로 추가한 관찰 도구 셋 중 마지막이었던 그 디렉터리입니다.

```bash
ls ~/.claude/sessions/
# 26316.json
# 26316.8baf91d0…<64자 16진수>…99170.key
# 29560.json
```

`<pid>.json` 이 프로세스의 명찰입니다. [관찰]

```bash
cd ~/.claude/sessions && python3 -c "
import json,glob
d=json.load(open(sorted(glob.glob('*.json'))[0]))
print(sorted(d))
print('socket:', d.get('messagingSocketPath'))"
```

```
['bridgeSessionId','cwd','entrypoint','kind','messagingSocketPath','name',
 'nameSince','nameSource','peerFeatures','peerProtocol','pid','procStart',
 'sessionId','startedAt','status','statusUpdatedAt','updatedAt','version']
socket: /tmp/cc-socks/26316.sock
```

**유닉스 도메인 소켓**입니다. 짝으로 있는 `.key` 파일이 인증에 쓰입니다. [추론]

### 메시지가 도착하는 모양

같은 세션의 팀메이트가 보내면 이렇게 감싸집니다. [관찰]

```xml
<teammate-message teammate_id="cc-tools-hooks" color="green" summary="...">
(내용)
</teammate-message>
```

다른 세션(다른 프로세스)에서 오면 발신자가 소켓 경로로 표시됩니다.

```xml
<cross-session-message from="uds:/tmp/cc-socks/<pid>.sock" from-name="..." from-mode="...">
```

에이전트가 유휴 상태가 되면 JSON 통지가 옵니다.

```json
{"type":"idle_notification","from":"cc-tools-hooks","idleReason":"available"}
```

`idleReason` 은 세 값입니다 — **`available`** (정상 완료), **`failed`** (에러로 중단), **`interrupted`**. 앞의 둘은 관찰했고 `interrupted` 는 못 봤습니다. [관찰]/[확인 못 함]

바이너리 문자열로도 확인됩니다.

```bash
python3 -c "
d=open('/tmp/s243.txt',encoding='utf-8',errors='replace').read()
for n in ['teammate-message','cross-session-message','idle_notification','notify_when_idle','ZZQuuxNotAThing']:
    print(f'{n:24s} 부분문자열={d.count(n):4d}  따옴표리터럴={d.count(chr(34)+n+chr(34)):3d}')"
```

```
teammate-message         부분문자열=   6  따옴표리터럴=  1
cross-session-message    부분문자열=  15  따옴표리터럴=  1
idle_notification        부분문자열=  13  따옴표리터럴=  6
notify_when_idle         부분문자열=  58  따옴표리터럴=  7
ZZQuuxNotAThing          부분문자열=   0  따옴표리터럴=  0
```

## 함정들

메시징은 **비동기이고, 보장이 약합니다.** 실제로 겪은 것들입니다. [관찰]

**1) `success: true` 는 "전달됐다"가 아닙니다.** 받는 쪽 **받은편지함에 썼다**는 뜻입니다. 상대가 언제 읽을지는 별개입니다.

**2) 상대가 바쁘면 오래 걸립니다.** 조사 중 메시지 하나가 **55 분** 뒤에야 처리된 사례가 있었습니다. 받는 쪽이 긴 작업 중이었기 때문입니다.

**3) 메시지 두 개가 한 턴으로 합쳐질 수 있습니다.** 연달아 보내면 상대가 한 번에 받습니다.

**4) `notify_when_idle` 은 팀메이트에게는 안 통합니다.** 바이너리에 그렇게 적혀 있고, 구독이 실패하면 **메시지 자체도 전달되지 않습니다.**

> **설계 교훈:** 메시징을 **동기 RPC 처럼 쓰면 안 됩니다.** "보냈으니 곧 답이 오겠지"를 전제하면 깨집니다. 보내고 잊어버린 뒤, 통지가 오면 그때 처리하는 구조가 맞습니다. 1편에서 본 **"do NOT sleep, poll"** 과 같은 원칙입니다.

## 정리

- 에이전트 여럿이 **파일을 고치면** 한 에이전트 안의 파일 상태 추적으로는 못 막습니다.
- **`isolation: worktree`** 는 에이전트마다 git worktree 를 줍니다. 평범한 `git worktree add` 와 같은 구조이고, 도는 동안 `locked` 입니다.
- **변경은 자동으로 돌아오지 않습니다.** 경로와 브랜치 이름만 돌아옵니다. 가져오는 건 여러분 몫입니다.
- **아무것도 안 바꿨으면 자동 삭제**되고 `.meta.json` 에 `worktreeCleanlyRemoved: true` 만 남습니다. 단 **untracked 부산물 하나만 있어도** 정리가 안 됩니다.
- 손으로 지우면 **브랜치가 남습니다.**
- 세션 간 메시징은 **유닉스 소켓** 기반이고, `~/.claude/sessions/<pid>.json` 이 명부입니다.
- **`success: true` 는 배달 완료가 아닙니다.** 55 분 지연도 봤습니다. 동기 RPC 처럼 쓰지 마세요.

## 확인 못 한 것

1. **worktree 의 분기 기준점.** 공식 문서는 "부모의 HEAD 가 아니라 기본 브랜치에서 분기한다"고 합니다. [문서] 제 실험 저장소는 브랜치가 하나뿐이라 **차이를 관찰하지 못했습니다.**
2. **`isolation: "remote"`** 는 재현하지 못했습니다.
3. **`.key` 파일의 용도.** 인증으로 보이지만 프로토콜을 확인하지 못했습니다. [추론]
4. **`idleReason: "interrupted"`** 는 발생시키지 못했습니다.
5. 실제 규모의 저장소에서 **worktree 체크아웃 비용**을 재지 않았습니다.

다음 편이 이 시즌의 마지막이자 목적지입니다. **언제 멀티에이전트가 손해인가** — 조율 비용, 대기 시간, 그리고 실패가 **결과가 너무 커서가 아니라 덜 전달돼서** 일어난다는 것을 실측으로 봅니다.

> 이전 편: [4편. Workflow ② — pipeline vs parallel, 그리고 재개 캐시](./04-workflow-patterns.md)
> 다음 편: [6편. 한계와 안티패턴 — 언제 멀티에이전트가 손해인가](./06-limits.md)
