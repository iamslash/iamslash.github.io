# Claude Code에서 Codex를 서브에이전트로 쓰기

> 이 글에서 배우는 것: 다른 회사 모델에게 일을 넘기는 법. 실습 5분.

Claude Code로 코딩하다 막힐 때가 있습니다. 같은 모델에게 다시 물어도 **같은 방식으로 틀립니다.**

이럴 때 **다른 모델**에게 한 번 더 보게 하면 좋습니다. OpenAI의 Codex를 Claude Code 안에서 부를 수 있습니다.

---

## 1. 준비

Codex CLI가 필요합니다.

```bash
npm install -g @openai/codex
codex login
```

확인:

```bash
codex --version
# codex-cli 0.149.1
```

ChatGPT 계정(무료 포함)이나 OpenAI API 키가 있어야 하고, **사용량은 Codex 쪽 한도에서 차감**됩니다.

---

## 2. 실습 — 직접 불러보기

서브에이전트로 감싸기 전에, **Codex를 손으로 한 번 불러봅니다.** 이게 되면 나머지는 포장일 뿐입니다.

버그가 있는 파일을 하나 만듭니다.

```bash
mkdir codexlab && cd codexlab
git init -q .                       # ← 이거 중요합니다. 이유는 아래에

cat > sum.py <<'EOF'
def average(nums):
    return sum(nums) / len(nums)
EOF
```

Codex에게 물어봅니다.

```bash
codex exec --sandbox read-only \
  "sum.py 의 average 함수는 어떤 입력에서 터지나? 한 문장으로 답하라." < /dev/null
```

실제 출력입니다. [관찰]

```
codex
`sum.py`의 구현만 확인해 실패 입력을 한 문장으로 요약하겠습니다.
exec
/bin/zsh -lc "sed -n '1,200p' sum.py"
 succeeded in 0ms:
def average(nums):
    return sum(nums) / len(nums)

codex
빈 리스트(또는 길이가 0인 입력)를 주면 0으로 나누어 `ZeroDivisionError`가 발생한다.
```

(문구는 실행할 때마다 조금씩 다릅니다. 요지가 같으면 정상입니다.)

**Codex가 스스로 파일을 읽고 답했습니다.** `--sandbox read-only` 라서 읽기만 하고 고치지는 않습니다 — 남의 모델에게 처음 일을 맡길 때 좋은 기본값입니다.

### 🚨 여기서 두 번 막힙니다

**① git 저장소가 아니면 거부합니다.**

```
Not inside a trusted directory and --skip-git-repo-check was not specified.
```

`git init` 을 먼저 하거나 `--skip-git-repo-check` 를 붙이세요. 실수로 작업물을 날리지 않게 하는 안전장치입니다.

**② `< /dev/null` 을 빼면 멈춘 것처럼 보입니다.** 프롬프트를 인자로 줘도 Codex는 stdin을 추가로 읽으려 합니다(`Reading additional input from stdin...`). 스크립트에서 부를 땐 꼭 막아주세요.

---

## 3. 서브에이전트로 만들기

방금 명령을 **에이전트 파일 하나**로 감싸면, 그때부터는 Claude에게 말로 시킬 수 있습니다.

`.claude/agents/codex.md` 를 만듭니다.

```markdown
---
name: codex
description: 다른 모델의 시선이 필요할 때. 버그 원인 파악이나 코드 검토를 Codex에게 넘긴다.
tools: Bash
---

너는 Codex에게 일을 넘기는 얇은 전달자다.

사용자의 요청을 `codex exec` 명령 **한 번**으로 전달하고, 그 출력을 그대로 보고하라.

    codex exec --sandbox read-only "<요청>" < /dev/null

직접 파일을 읽거나 분석하지 마라. 전달만 하라.
```

Claude Code를 다시 띄우면 이렇게 쓸 수 있습니다.

```
codex 서브에이전트로 sum.py 를 검토해줘
```

**핵심은 `tools: Bash` 한 줄입니다.** 서브에이전트에게 Bash만 주면, 그 안에서 무엇을 부르든 상관없습니다. Codex든 다른 CLI든요.

> **직접 만들기 싫다면** OpenAI가 만든 플러그인이 있습니다. `/plugin marketplace add openai/codex-plugin-cc` 로 설치하면 `/codex:review` 같은 명령과 `codex-rescue` 서브에이전트가 딸려옵니다.

---

## 왜 굳이

**같은 모델은 같은 곳에서 틀립니다.** 제가 놓친 것을 제가 다시 볼 확률은 낮습니다. 다른 모델은 다른 곳에서 틀리니, 겹치지 않는 실수를 잡아줍니다.

그래서 **구현보다 검토에 쓸 때 값어치가 큽니다.**

---

## 확인 못 한 것

- 위 출력은 **codex-cli 0.149.1** 기준입니다. CLI 옵션은 자주 바뀝니다.
- **직접 만든 서브에이전트를 실제로 띄워보지는 못했습니다.** `codex exec` 호출과 파일 형식(공식 `codex-rescue` 에이전트와 동일한 프론트매터)까지만 확인했습니다.
- 요금과 사용량 한도는 확인하지 않았습니다. Codex 쪽 정책을 직접 보세요.

---

## 정리

- **`codex exec` 한 줄이 전부입니다.** 서브에이전트는 그걸 말로 부르기 좋게 감싼 것뿐입니다.
- **`git init` 먼저**, 그리고 **`< /dev/null`**. 이 둘에서 대부분 막힙니다.
- 처음에는 **`--sandbox read-only`** 로 시작하세요.
- **구현보다 검토**에 쓰는 게 낫습니다.
