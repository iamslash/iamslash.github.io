# 발행 트래커 — Claude Code 내부 구조

이 디렉터리(`drafts/claude-code-internals/`)의 글은 전부 **draft** 다. mdBook 은 `book.toml` 의 `src = "src"`
설정에 따라 `src/` 만 빌드하므로, 여기 있는 글은 사이트에 절대 뜨지 않는다(소스는 공개 repo 엔 보임).
한 편을 검수·확정하면 아래 순서대로 하나씩 발행한다.

**주의:** mdBook 은 `src/SUMMARY.md` 에 링크된 페이지만 렌더링한다. 파일을 `src/` 로 옮기더라도
SUMMARY 에 등록하기 전엔 사이트에 안 뜬다.

## 발행 방법 (한 편씩)

1. 파일을 src 로 이동:
   `mv drafts/claude-code-internals/<파일> src/ko/claude-code-internals/`
   (첫 발행이면 먼저 `mkdir -p src/ko/claude-code-internals`)
2. `src/SUMMARY.md` 의 `# 한국어` 섹션 아래에 해당 줄을 추가.
   첫 발행 시 소제목 헤더 `# Claude Code 내부 구조` 도 함께 추가.
3. 커밋 + push → GitHub Actions 가 빌드·배포.

로컬 미리보기: 보고 싶은 draft 를 임시로 src 로 옮겨 `mdbook serve` 로 확인 후 되돌리거나,
발행 직전에 옮겨서 확인한다. (`mdbook` 미설치 시 `cargo install mdbook`)

**순서 주의:** 각 편은 말미에 "다음 편" 링크를 가지므로, 다음 편이 미발행이면 그 링크가 404 가 된다.
**순서대로 발행**하고, 마지막 편은 다음 링크가 없다.

## 첫 발행 시 SUMMARY.md 에 추가할 소제목

```
# Claude Code 내부 구조
```

## 읽기 순서와 발행 목록

- [ ] **00** — `mv drafts/claude-code-internals/00-prologue.md src/ko/claude-code-internals/`
  - SUMMARY: `- [프롤로그 — Claude Code는 결국 while 루프 하나다](./ko/claude-code-internals/00-prologue.md)`
- [ ] **01** — `mv drafts/claude-code-internals/01-prompt-to-messages.md src/ko/claude-code-internals/`
  - SUMMARY: `- [엔터를 치면 무슨 일이 일어나는가](./ko/claude-code-internals/01-prompt-to-messages.md)`
- [ ] **02** — `mv drafts/claude-code-internals/02-request-body.md src/ko/claude-code-internals/`
  - SUMMARY: `- [요청 바디 해부 — LLM에게 실제로 보내는 것](./ko/claude-code-internals/02-request-body.md)`
- [ ] **03** — `mv drafts/claude-code-internals/03-streaming-and-stop-reason.md src/ko/claude-code-internals/`
  - SUMMARY: `- [응답 — SSE 스트리밍과 stop_reason](./ko/claude-code-internals/03-streaming-and-stop-reason.md)`
- [ ] **04** — `mv drafts/claude-code-internals/04-agent-loop.md src/ko/claude-code-internals/`
  - SUMMARY: `- [Agent loop — while 루프 하나가 전부다](./ko/claude-code-internals/04-agent-loop.md)`
- [ ] **05** — `mv drafts/claude-code-internals/05-tools.md src/ko/claude-code-internals/`
  - SUMMARY: `- [Tool — 모델은 함수를 부르지 않는다](./ko/claude-code-internals/05-tools.md)`
- [ ] **06** — `mv drafts/claude-code-internals/06-hooks.md src/ko/claude-code-internals/`
  - SUMMARY: `- [Hook — 하네스에 내 코드를 꽂는 자리](./ko/claude-code-internals/06-hooks.md)`
- [ ] **07** — `mv drafts/claude-code-internals/07-subagents.md src/ko/claude-code-internals/`
  - SUMMARY: `- [서브에이전트 — 컨텍스트를 지키는 격리](./ko/claude-code-internals/07-subagents.md)`
- [ ] **08** — `mv drafts/claude-code-internals/08-agent-types.md src/ko/claude-code-internals/`
  - SUMMARY: `- [에이전트 종류 — 빌트인 에이전트 목록](./ko/claude-code-internals/08-agent-types.md)`
- [ ] **09** — `mv drafts/claude-code-internals/09-workflow-and-skills.md src/ko/claude-code-internals/`
  - SUMMARY: `- [Workflow와 확장 표면 — Skill, 슬래시 커맨드, plan mode](./ko/claude-code-internals/09-workflow-and-skills.md)`
- [ ] **10 (부록)** — `mv drafts/claude-code-internals/10-claude-dir.md src/ko/claude-code-internals/`
  - SUMMARY: `- [부록. ~/.claude 안내 지도](./ko/claude-code-internals/10-claude-dir.md)`
- [ ] **11 (캡스톤)** — `mv drafts/claude-code-internals/11-build-your-own.md src/ko/claude-code-internals/`
  - SUMMARY: `- [직접 만들어보기 — 150줄짜리 미니 Claude Code](./ko/claude-code-internals/11-build-your-own.md)`

## 시리즈 구성 메모

- **관통 명제:** "LLM API 는 상태가 없다. Claude Code 는 매 턴 전부를 다시 보내는 `while` 루프 하나다."
  0편에서 세우고, 이후 모든 편이 그 루프 주변에 무엇이 붙어 있는지를 설명하는 구조.
- **눈높이:** Junior Software Engineer. LLM API 를 한 번도 직접 호출해본 적 없는 독자를 가정한다.
- **범위:** **builtin Claude Code 만.** 플러그인·서드파티 레이어(oh-my-claudecode 등)는 다루지 않는다.
  관찰 시 `CLAUDE_CONFIG_DIR` 을 빈 디렉터리로 지정해 플러그인이 로드되지 않은 상태를 봐야 한다.
- **버전 고정:** 전부 **2.1.243** 기준. 내부 구조는 버전마다 바뀌므로 각 편 머리말에 버전을 명시한다.
- **증거 라벨:** 모든 주장에 `[관찰]` / `[문서]` / `[추론]` 중 하나를 붙인다. 확인 못 한 것은
  각 편 말미에 "확인 못 한 것" 으로 정직하게 남긴다.
- **관찰 도구 3종** (0편에서 세팅):
  1. 세션 트랜스크립트 `~/.claude/projects/*/*.jsonl` + `jq`
  2. `claude --debug api`
  3. 로컬 싱크 프록시 — `ANTHROPIC_BASE_URL=http://127.0.0.1:8931` + 가짜 API 키로 실제 요청 바디 캡처

## 각 편의 "반전" (독자가 가져갈 한 문장)

| 편 | 반전 |
|---|---|
| 00 | LLM 은 기억하지 않는다. 매번 전부 다시 보낸다 |
| 01 | `@file` 은 툴 호출이 아니다 — 하네스가 미리 읽어 합성 텍스트를 심는다 |
| 02 | `CLAUDE.md` 는 system 프롬프트에 없다. 반대로 `gitStatus` 는 system 프롬프트에 있다 |
| 03 | `stop_reason` 이 루프를 계속 돌릴지 정하는 단 하나의 신호다 |
| 04 | 툴은 스트리밍이 끝난 뒤가 아니라 **도중에** 디스패치된다 |
| 05 | 모델은 함수를 부르지 않는다. JSON 을 뱉을 뿐이고 실행은 전부 하네스가 한다 |
| 06 | 훅 출력은 `<system-reminder>` 가 되어 모델 컨텍스트로 들어간다 |
| 07 | 서브에이전트가 12만 토큰을 쓰고 부모에겐 한 줄만 돌려준다 |
| 08 | 빌트인 에이전트 목록은 버전마다 바뀐다 (2.1.243 에서 하나가 사라졌다) |
| 09 | 슬래시 커맨드는 균일한 텍스트 확장이 아니다 — 로컬 실행형은 모델을 다시 부르지도 않는다 |
| 10 | 빈 설정으로 실행하면 네 개만 생긴다 — 나머지는 내가 써온 기록이다 |
| 11 | 서브에이전트 격리의 정체는 '새 리스트 하나'다 |

앞으로 새로 쓰는 글도 기본적으로 이 `drafts/` 아래에 두고, 검수 후 같은 방식으로 발행한다.
