# 발행 트래커 — 밑바닥부터 이해하는 A/B 테스트 통계

이 디렉터리(`drafts/ab-testing/`)의 글은 전부 **draft** 다. mdBook 은 `book.toml` 의 `src = "src"`
설정에 따라 `src/` 만 빌드하므로, 여기 있는 글은 사이트에 절대 뜨지 않는다(소스는 공개 repo 엔 보임).
한 편을 검수·확정하면 아래 순서대로 하나씩 발행한다.

**주의:** mdBook 은 `src/SUMMARY.md` 에 링크된 페이지만 렌더링한다. 즉 파일을 `src/` 로 옮기더라도
SUMMARY 에 등록하기 전엔 사이트에 안 뜬다. 지금은 아무것도 SUMMARY 에 없으므로 **전편 안전하게 미발행** 상태다.

## 발행 방법 (한 편씩)

1. 파일을 src 로 이동:
   `mv drafts/ab-testing/<파일> src/ko/ab-testing/`
   (첫 발행이면 먼저 `mkdir -p src/ko/ab-testing`)
2. `src/SUMMARY.md` 의 `# 한국어` 섹션 아래에 해당 줄을 추가.
   첫 발행 시 소제목 헤더 `# 밑바닥부터 이해하는 A/B 테스트 통계` 도 함께 추가.
3. 커밋 + push → GitHub Actions 가 빌드·배포.

로컬 미리보기: 보고 싶은 draft 를 임시로 src 로 옮겨 `mdbook serve` 로 확인 후 되돌리거나,
발행 직전에 옮겨서 확인한다. (`mdbook` 미설치 시 `cargo install mdbook`)

**순서 주의:** 순서대로 내는 중이라면, 먼저 발행된 글의 "다음 편" 링크가 아직 미발행인 다음 편을
가리켜 그 순간엔 404 가 될 수 있다(다음 편을 발행하면 해소). 신경 쓰이면 다음 편까지 함께 발행하자.
(12편은 "다음" 링크가 없으므로 이 문제에서 자유롭다.)

## 첫 발행 시 SUMMARY.md 에 추가할 소제목

```
# 밑바닥부터 이해하는 A/B 테스트 통계
```

## 읽기 순서와 발행 목록 (체크하며 진행)

- [ ] **00** — `mv drafts/ab-testing/00-prologue.md src/ko/ab-testing/`
  - SUMMARY: `- [프롤로그 — 엔지니어를 위한 A/B 통계 지도](./ko/ab-testing/00-prologue.md)`
- [ ] **01** — `mv drafts/ab-testing/01-summary-statistics.md src/ko/ab-testing/`
  - SUMMARY: `- [데이터를 숫자 몇 개로 요약하기](./ko/ab-testing/01-summary-statistics.md)`
- [ ] **02** — `mv drafts/ab-testing/02-normal-distribution-clt.md src/ko/ab-testing/`
  - SUMMARY: `- [정규분포와 중심극한정리](./ko/ab-testing/02-normal-distribution-clt.md)`
- [ ] **03** — `mv drafts/ab-testing/03-standard-error-confidence-interval.md src/ko/ab-testing/`
  - SUMMARY: `- [일부로 전체 추측하기 — 표준오차와 신뢰구간](./ko/ab-testing/03-standard-error-confidence-interval.md)`
- [ ] **04** — `mv drafts/ab-testing/04-hypothesis-testing-pvalue.md src/ko/ab-testing/`
  - SUMMARY: `- [가설검정의 심장 (1) — 귀무가설과 p-value](./ko/ab-testing/04-hypothesis-testing-pvalue.md)`
- [ ] **05** — `mv drafts/ab-testing/05-significance-errors.md src/ko/ab-testing/`
  - SUMMARY: `- [가설검정의 심장 (2) — 유의수준과 1종·2종 오류](./ko/ab-testing/05-significance-errors.md)`
- [ ] **06** — `mv drafts/ab-testing/06-z-test-t-test.md src/ko/ab-testing/`
  - SUMMARY: `- [p-value를 실제로 계산하기 — z-test와 t-test](./ko/ab-testing/06-z-test-t-test.md)`
- [ ] **07** — `mv drafts/ab-testing/07-power-sample-size-mde.md src/ko/ab-testing/`
  - SUMMARY: `- [실험을 설계하기 — 검정력·표본 크기·MDE](./ko/ab-testing/07-power-sample-size-mde.md)`
- [ ] **08** — `mv drafts/ab-testing/08-peeking-sequential-testing.md src/ko/ab-testing/`
  - SUMMARY: `- [훔쳐보기의 함정 — peeking과 sequential testing](./ko/ab-testing/08-peeking-sequential-testing.md)`
- [ ] **09** — `mv drafts/ab-testing/09-multiple-comparisons-srm-guardrail.md src/ko/ab-testing/`
  - SUMMARY: `- [우연한 승자들 — 다중비교·SRM·가드레일](./ko/ab-testing/09-multiple-comparisons-srm-guardrail.md)`
- [ ] **10** — `mv drafts/ab-testing/10-cuped-variance-reduction.md src/ko/ab-testing/`
  - SUMMARY: `- [더 적은 사람으로 더 빨리 — CUPED와 분산감소](./ko/ab-testing/10-cuped-variance-reduction.md)`
- [ ] **11** — `mv drafts/ab-testing/11-frequentist-vs-bayesian.md src/ko/ab-testing/`
  - SUMMARY: `- [두 학파 — 빈도주의 vs 베이지안](./ko/ab-testing/11-frequentist-vs-bayesian.md)`
- [ ] **12** — `mv drafts/ab-testing/12-bandit-thompson-sampling.md src/ko/ab-testing/`
  - SUMMARY: `- [실험에서 자동화로 — Multi-armed Bandit과 Thompson Sampling](./ko/ab-testing/12-bandit-thompson-sampling.md)`

앞으로 새로 쓰는 글도 기본적으로 이 `drafts/` 아래에 두고, 검수 후 같은 방식으로 발행한다.
