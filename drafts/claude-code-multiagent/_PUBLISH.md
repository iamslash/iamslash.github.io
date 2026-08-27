# 발행 트래커 — Claude Code 멀티에이전트 (시즌 2)

이 디렉터리(`drafts/claude-code-multiagent/`)의 글은 전부 **draft** 다. mdBook 은 `src/` 만 빌드하므로
여기 있는 글은 사이트에 뜨지 않는다(소스는 공개 repo 엔 보임).

**선행 시리즈:** `drafts/claude-code-internals/` (시즌 1, 12편). 이 시즌은 시즌 1 을 읽었다고 가정한다.

## 발행 방법 (한 편씩)

1. `mv drafts/claude-code-multiagent/<파일> src/ko/claude-code-multiagent/`
   (첫 발행이면 먼저 `mkdir -p src/ko/claude-code-multiagent`)
2. `src/SUMMARY.md` 의 `# 한국어` 섹션 아래에 해당 줄 추가.
   첫 발행 시 소제목 헤더 `# Claude Code 멀티에이전트` 도 함께 추가.
3. 커밋 + push → GitHub Actions 가 빌드·배포.

**순서 주의:** 각 편이 "다음 편" 링크를 가지므로 순서대로 발행한다.
0편은 시즌 1 로 돌아가는 링크(`../claude-code-internals/`)를 가지므로 **시즌 1 이 먼저 발행돼 있어야 한다.**

## 첫 발행 시 SUMMARY.md 에 추가할 소제목

```
# Claude Code 멀티에이전트
```

## 읽기 순서와 발행 목록

- [ ] **00** — `mv drafts/claude-code-multiagent/00-prologue.md src/ko/claude-code-multiagent/`
  - SUMMARY: `- [프롤로그 — 멀티에이전트는 병렬화가 아니다](./ko/claude-code-multiagent/00-prologue.md)`
- [ ] **01** — `01-delegation.md`
  - SUMMARY: `- [위임의 해부 — 브리핑이 전부다](./ko/claude-code-multiagent/01-delegation.md)`
- [ ] **02** — `02-isolation-spectrum.md`
  - SUMMARY: `- [격리의 스펙트럼 — fork, observer, 에이전트 메모리](./ko/claude-code-multiagent/02-isolation-spectrum.md)`
- [ ] **03** — `03-workflow-contract.md`
  - SUMMARY: `- [Workflow ① — 결정적 오케스트레이션의 계약](./ko/claude-code-multiagent/03-workflow-contract.md)`
- [ ] **04** — `04-workflow-patterns.md`
  - SUMMARY: `- [Workflow ② — pipeline vs parallel, 그리고 재개 캐시](./ko/claude-code-multiagent/04-workflow-patterns.md)`
- [ ] **05** — `05-worktree-cross-session.md`
  - SUMMARY: `- [worktree 격리와 교차 세션 메시징](./ko/claude-code-multiagent/05-worktree-cross-session.md)`
- [ ] **06** — `06-limits.md`
  - SUMMARY: `- [한계와 안티패턴 — 언제 멀티에이전트가 손해인가](./ko/claude-code-multiagent/06-limits.md)`

## 시즌 구성 메모

- **관통 명제:** "멀티에이전트는 병렬화가 아니라 **컨텍스트 분할**이다."
  대부분의 사람이 속도 때문에 쓴다고 생각하는데, 실측하면 진짜 이득은 컨텍스트다.
- **목적지는 6편.** 멀티에이전트 콘텐츠는 대개 응원가다. "이럴 땐 쓰지 마라"를 실측으로 쓰는 것이 이 시즌의 차별점.
- **눈높이:** Junior Software Engineer. 시즌 1 을 읽었다고 가정하되, 핵심은 다시 짚는다.
- **버전 표기 주의:** 조사 중 머신이 2.1.243 → 2.1.246 으로 자동 업데이트됐고,
  2.1.246 부터 JS 일부가 바이트코드로 컴파일되어 `strings` 추출이 약해졌다.
  → **코드 인용은 2.1.243, 동작 실험은 2.1.246** 으로 나누어 표기한다.
- **증거 라벨:** `[관찰]` / `[문서]` / `[추론]`. 각 편 말미에 "확인 못 한 것" 유지.

## 관찰 도구 (시즌 1 의 3종 + 3종)

1~3. 트랜스크립트 · `--debug api` · 로컬 싱크 프록시 (시즌 1 0편)
4. **자식 트랜스크립트** — `~/.claude/projects/*/*/subagents/`
5. **워크플로 저널** — `find ~/.claude/projects -name journal.jsonl`
6. **세션 명부** — `~/.claude/sessions/`

## 각 편의 "반전"

| 편 | 반전 |
|---|---|
| 00 | 262건에서 자식 컨텍스트 합이 1,738만 토큰, 부모에겐 약 1/642 만 돌아왔다 |
| 01 | 자식의 대답은 **untrusted 로 명시적으로 프레이밍**된다 |
| 02 | `fork` 만 부모 컨텍스트를 상속한다 — 격리 원칙의 유일한 예외 |
| 03 | `Workflow` 는 플러그인이 아니라 **빌트인**이다 |
| 04 | `pipeline` 에는 배리어가 없다 — 저널이 증명한다 |
| 05 | 워크트리는 변경을 자동으로 되돌려주지 않는다 |
| 06 | 실패는 결과가 **너무 커서**가 아니라 **덜 전달돼서** 일어난다 |

## 조사 산출물 (집필 재료)

`scratchpad/` 에 조사 보고서 4종이 있다. 세션이 바뀌면 사라지므로, 인용할 실측치는
글에 옮겨 적을 때 **반드시 다시 실행해서 확인**할 것.

- `s2-report-01-nesting-worktree-memory.md` — 중첩 깊이 3 재현, worktree, 에이전트 메모리
- `s2-report-02-fork-observer-gates.md` — fork/observer/coordinator, GrowthBook 게이트 열거법
- `s2-report-03-crosssession-limits.md` — 교차 세션 메시징, 한계 수치, 압축 임계값
- `s2-report-04-workflow-traces.md` — Workflow 6회 직접 실행 트레이스
