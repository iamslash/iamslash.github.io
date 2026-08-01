# 발행 트래커 — AI 답변을 채점하는 법 (LLM-as-a-Judge)

이 디렉터리(`drafts/llm-as-a-judge/`)의 글은 전부 **draft** 다. mdBook 은 `book.toml` 의 `src = "src"`
설정에 따라 `src/` 만 빌드하므로, 여기 있는 글은 사이트에 절대 뜨지 않는다(소스는 공개 repo 엔 보임).
한 편을 검수·확정하면 아래 순서대로 하나씩 발행한다.

**주의:** mdBook 은 `src/SUMMARY.md` 에 링크된 페이지만 렌더링한다. 즉 파일을 `src/` 로 옮기더라도
SUMMARY 에 등록하기 전엔 사이트에 안 뜬다. 지금은 아무것도 SUMMARY 에 없으므로 **전편 안전하게 미발행** 상태다.

## 발행 방법 (한 편씩)

1. 파일을 src 로 이동:
   `mv drafts/llm-as-a-judge/<파일> src/ko/llm-as-a-judge/`
   (첫 발행이면 먼저 `mkdir -p src/ko/llm-as-a-judge`)
2. `src/SUMMARY.md` 의 `# 한국어` 섹션 아래에 해당 줄을 추가.
   첫 발행 시 소제목 헤더 `# AI 답변을 채점하는 법 — LLM-as-a-Judge` 도 함께 추가.
3. 커밋 + push → GitHub Actions 가 빌드·배포.

로컬 미리보기: 보고 싶은 draft 를 임시로 src 로 옮겨 `mdbook serve` 로 확인 후 되돌리거나,
발행 직전에 옮겨서 확인한다. (`mdbook` 미설치 시 `cargo install mdbook`)

**순서 주의:** 각 편은 "다음" 링크를 가지고 있어서, 다음 편이 미발행이면 그 링크가 404 가 된다.
신경 쓰이면 두 편씩 묶어서 발행하자. (7편은 "다음" 링크가 없다.)

## 첫 발행 시 SUMMARY.md 에 추가할 소제목

```
# AI 답변을 채점하는 법 — LLM-as-a-Judge
```

## 읽기 순서와 발행 목록 (체크하며 진행)

- [ ] **00** — `mv drafts/llm-as-a-judge/00-prologue.md src/ko/llm-as-a-judge/`
  - SUMMARY: `- [프롤로그 — "이 답변, 좋은 건가요?"](./ko/llm-as-a-judge/00-prologue.md)`
- [ ] **01** — `mv drafts/llm-as-a-judge/01-what-to-score.md src/ko/llm-as-a-judge/`
  - SUMMARY: `- [무엇을 채점할 것인가 — 테스트 케이스와 데이터셋](./ko/llm-as-a-judge/01-what-to-score.md)`
- [ ] **02** — `mv drafts/llm-as-a-judge/02-human-labeling.md src/ko/llm-as-a-judge/`
  - SUMMARY: `- [사람이 먼저 채점한다](./ko/llm-as-a-judge/02-human-labeling.md)`
- [ ] **03** — `mv drafts/llm-as-a-judge/03-build-a-judge.md src/ko/llm-as-a-judge/`
  - SUMMARY: `- [LLM judge 만들기](./ko/llm-as-a-judge/03-build-a-judge.md)`
- [ ] **04** — `mv drafts/llm-as-a-judge/04-validate-the-judge.md src/ko/llm-as-a-judge/`
  - SUMMARY: `- [judge를 믿어도 되는가](./ko/llm-as-a-judge/04-validate-the-judge.md)`
- [ ] **05** — `mv drafts/llm-as-a-judge/05-judge-biases.md src/ko/llm-as-a-judge/`
  - SUMMARY: `- [judge의 함정 — 편향과 pairwise](./ko/llm-as-a-judge/05-judge-biases.md)`
- [ ] **06** — `mv drafts/llm-as-a-judge/06-ab-loop.md src/ko/llm-as-a-judge/`
  - SUMMARY: `- [프롬프트 A와 B, 어느 쪽이 나은가](./ko/llm-as-a-judge/06-ab-loop.md)`
- [ ] **07** — `mv drafts/llm-as-a-judge/07-papers-and-tools.md src/ko/llm-as-a-judge/`
  - SUMMARY: `- [논문과 오픈소스 — 더 공부할 거리](./ko/llm-as-a-judge/07-papers-and-tools.md)`

## 시리즈 구성 메모

- **관통 예제:** 온라인 원두 쇼핑몰 "콩마켓"의 고객 상담 챗봇 "콩돌이".
  (A/B 테스트 시리즈의 "콩마켓"과 세계관을 공유하되, 두 시리즈는 서로 독립적으로 읽힌다.)
- **눈높이:** Junior Software Engineer. 통계 용어는 손계산으로 풀고, 코드는 실행 가능한 형태로.
- **핵심 축:** judge 를 만드는 법(3편)보다 **judge 를 검증하는 법(4편)** 이 무게중심.
- **각 편 끝의 "도구에서는 어떻게 부르나"** 는 A/B 시리즈의 "프레임워크에서 어디에 쓰이나"와 같은 역할.

앞으로 새로 쓰는 글도 기본적으로 이 `drafts/` 아래에 두고, 검수 후 같은 방식으로 발행한다.
