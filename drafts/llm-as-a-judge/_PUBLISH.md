# 발행 트래커 — AI 답변을 채점하는 법 (LLM-as-a-Judge)

이 디렉터리(`drafts/llm-as-a-judge/`)의 글은 전부 **draft** 다. mdBook 은 `book.toml` 의 `src = "src"`
설정에 따라 `src/` 만 빌드하므로, 여기 있는 글은 사이트에 절대 뜨지 않는다(소스는 공개 repo 엔 보임).
한 편을 검수·확정하면 아래 순서대로 하나씩 발행한다.

**주의:** mdBook 은 `src/SUMMARY.md` 에 링크된 페이지만 렌더링한다. 파일을 `src/` 로 옮기더라도
SUMMARY 에 등록하기 전엔 사이트에 안 뜬다.

## 발행 방법 (한 편씩)

1. 파일을 src 로 이동:
   `mv drafts/llm-as-a-judge/<파일> src/ko/llm-as-a-judge/`
   (첫 발행이면 먼저 `mkdir -p src/ko/llm-as-a-judge`)
2. `src/SUMMARY.md` 의 `# 한국어` 섹션 아래에 해당 줄을 추가.
   첫 발행 시 소제목 헤더 `# AI 답변을 채점하는 법 — LLM-as-a-Judge` 도 함께 추가.
3. 커밋 + push → GitHub Actions 가 빌드·배포.

로컬 미리보기: 보고 싶은 draft 를 임시로 src 로 옮겨 `mdbook serve` 로 확인 후 되돌리거나,
발행 직전에 옮겨서 확인한다. (`mdbook` 미설치 시 `cargo install mdbook`)

**순서 주의:** 1·2편은 "다음" 링크를 가지므로, 다음 편이 미발행이면 그 링크가 404 가 된다.
세 편이 하나의 흐름이므로 **한꺼번에 발행하는 것을 권한다.**

## 첫 발행 시 SUMMARY.md 에 추가할 소제목

```
# AI 답변을 채점하는 법 — LLM-as-a-Judge
```

## 읽기 순서와 발행 목록

- [ ] **01** — `mv drafts/llm-as-a-judge/01-judge-and-rubric.md src/ko/llm-as-a-judge/`
  - SUMMARY: `- [LLM 답변을 자동으로 채점하기 — judge와 rubric](./ko/llm-as-a-judge/01-judge-and-rubric.md)`
- [ ] **02** — `mv drafts/llm-as-a-judge/02-tune-the-rubric.md src/ko/llm-as-a-judge/`
  - SUMMARY: `- [rubric 튜닝 — judge를 사람 기준에 맞추기](./ko/llm-as-a-judge/02-tune-the-rubric.md)`
- [ ] **03** — `mv drafts/llm-as-a-judge/03-compare-prompts.md src/ko/llm-as-a-judge/`
  - SUMMARY: `- [프롬프트 A와 B, 어느 쪽이 나은가](./ko/llm-as-a-judge/03-compare-prompts.md)`

## 시리즈 구성 메모

- **3막 구조:** ① judge 만들기 → ② 사람 기준에 맞춰 rubric 튜닝 → ③ 튜닝 끝난 judge 를 동결하고 프롬프트 평가.
  **튜닝과 평가를 동시에 하면 안 된다**는 것이 이 구조의 핵심이며, 각 편의 경계가 그 순서를 강제한다.
- **관통 예제:** 온라인 원두 쇼핑몰 "콩마켓"의 고객 상담 챗봇 "콩돌이".
  (A/B 테스트 시리즈의 "콩마켓"과 세계관을 공유하되, 두 시리즈는 독립적으로 읽힌다.)
- **눈높이:** Junior Software Engineer. 통계는 손계산으로 풀고, 코드는 실행 가능한 형태로.
- **무게중심은 2편.** judge 를 만드는 것(1편)은 반나절이면 되지만, 검증(2편)을 건너뛰면 전부 무의미해진다.

앞으로 새로 쓰는 글도 기본적으로 이 `drafts/` 아래에 두고, 검수 후 같은 방식으로 발행한다.
