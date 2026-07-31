# 발행 트래커 — 미국 정착 가이드

이 디렉터리(`drafts/us-life/`)의 글은 전부 **draft** 다. mdBook 은 `book.toml` 의 `src = "src"`
설정에 따라 `src/` 만 빌드하므로, 여기 있는 글은 사이트에 절대 뜨지 않는다(소스는 공개 repo 엔 보임).

**현재 상태: 제목만 확정된 스텁.** 각 파일에는 `# 제목` 한 줄만 있고 본문은 아직 없다.
본문을 작성·검수·확정한 편부터 아래 순서대로 하나씩 발행한다.

**주의:** mdBook 은 `src/SUMMARY.md` 에 링크된 페이지만 렌더링한다. 즉 파일을 `src/` 로 옮기더라도
SUMMARY 에 등록하기 전엔 사이트에 안 뜬다. 지금은 아무것도 SUMMARY 에 없으므로 **전편 안전하게 미발행** 상태다.

## 발행 방법 (한 편씩)

1. 파일을 src 로 이동:
   `mv drafts/us-life/<파일> src/ko/us-life/`
   (첫 발행이면 먼저 `mkdir -p src/ko/us-life`)
2. `src/SUMMARY.md` 의 `# 한국어` 섹션 아래에 해당 줄을 추가.
   첫 발행 시 소제목 헤더 `# 미국 정착 가이드` 도 함께 추가.
3. 커밋 + push → GitHub Actions 가 빌드·배포.

로컬 미리보기: 보고 싶은 draft 를 임시로 src 로 옮겨 `mdbook serve` 로 확인 후 되돌리거나,
발행 직전에 옮겨서 확인한다. (`mdbook` 미설치 시 `cargo install mdbook`)

**순서 주의:** 본문에 "다음 편" 링크를 넣는 경우, 먼저 발행된 글의 링크가 아직 미발행인 다음 편을
가리켜 그 순간엔 404 가 될 수 있다. 신경 쓰이면 다음 편까지 함께 발행하자.

## 첫 발행 시 SUMMARY.md 에 추가할 소제목

```
# 미국 정착 가이드
```

## 읽기 순서와 발행 목록 (체크하며 진행)

순서는 정착 시간순이다. 주제 묶음: 신분/행정(01–03), 금융(04–06), 주거(07–11),
통신(12–13), 자동차(14–16), 생활(17–21), 세금(22).

- [ ] **01** — `mv drafts/us-life/01-ssn.md src/ko/us-life/`
  - SUMMARY: `- [SSN(사회보장번호) 발급받기](./ko/us-life/01-ssn.md)`
- [ ] **02** — `mv drafts/us-life/02-drivers-license.md src/ko/us-life/`
  - SUMMARY: `- [DMV 운전면허 획득하기](./ko/us-life/02-drivers-license.md)`
- [ ] **03** — `mv drafts/us-life/03-usps-mail.md src/ko/us-life/`
  - SUMMARY: `- [USPS 우편 사용하기](./ko/us-life/03-usps-mail.md)`
- [ ] **04** — `mv drafts/us-life/04-bank-account.md src/ko/us-life/`
  - SUMMARY: `- [은행 계좌 만들기](./ko/us-life/04-bank-account.md)`
- [ ] **05** — `mv drafts/us-life/05-credit-score.md src/ko/us-life/`
  - SUMMARY: `- [신용카드 만들기와 크레딧 스코어 쌓기](./ko/us-life/05-credit-score.md)`
- [ ] **06** — `mv drafts/us-life/06-money-apps.md src/ko/us-life/`
  - SUMMARY: `- [Zelle / Venmo 송금 앱 이해하기](./ko/us-life/06-money-apps.md)`
- [ ] **07** — `mv drafts/us-life/07-apartment-rent.md src/ko/us-life/`
  - SUMMARY: `- [아파트 렌트 구하기](./ko/us-life/07-apartment-rent.md)`
- [ ] **08** — `mv drafts/us-life/08-utilities.md src/ko/us-life/`
  - SUMMARY: `- [유틸리티 개통하기 — 전기·가스·수도](./ko/us-life/08-utilities.md)`
- [ ] **09** — `mv drafts/us-life/09-renters-insurance.md src/ko/us-life/`
  - SUMMARY: `- [렌터스 보험 가입하기](./ko/us-life/09-renters-insurance.md)`
- [ ] **10** — `mv drafts/us-life/10-trash.md src/ko/us-life/`
  - SUMMARY: `- [쓰레기 버리기 — 분리수거, 대형 폐기물](./ko/us-life/10-trash.md)`
- [ ] **11** — `mv drafts/us-life/11-e-waste.md src/ko/us-life/`
  - SUMMARY: `- [폐가전 버리기 — e-waste](./ko/us-life/11-e-waste.md)`
- [ ] **12** — `mv drafts/us-life/12-internet.md src/ko/us-life/`
  - SUMMARY: `- [인터넷 가입하기](./ko/us-life/12-internet.md)`
- [ ] **13** — `mv drafts/us-life/13-mobile-phone.md src/ko/us-life/`
  - SUMMARY: `- [휴대전화 가입하기 — 선불/후불, MVNO](./ko/us-life/13-mobile-phone.md)`
- [ ] **14** — `mv drafts/us-life/14-buying-a-car.md src/ko/us-life/`
  - SUMMARY: `- [자동차 사기 — 신차/중고, 딜러, 등록](./ko/us-life/14-buying-a-car.md)`
- [ ] **15** — `mv drafts/us-life/15-car-insurance.md src/ko/us-life/`
  - SUMMARY: `- [자동차 보험 가입하기](./ko/us-life/15-car-insurance.md)`
- [ ] **16** — `mv drafts/us-life/16-gas-station.md src/ko/us-life/`
  - SUMMARY: `- [주유소·세차·정비 이용하기](./ko/us-life/16-gas-station.md)`
- [ ] **17** — `mv drafts/us-life/17-grocery.md src/ko/us-life/`
  - SUMMARY: `- [마트 가보기 — 그로서리, Costco, 한인마트](./ko/us-life/17-grocery.md)`
- [ ] **18** — `mv drafts/us-life/18-online-shopping.md src/ko/us-life/`
  - SUMMARY: `- [온라인 쇼핑 — Amazon 중심](./ko/us-life/18-online-shopping.md)`
- [ ] **19** — `mv drafts/us-life/19-tipping.md src/ko/us-life/`
  - SUMMARY: `- [팁 문화 이해하기](./ko/us-life/19-tipping.md)`
- [ ] **20** — `mv drafts/us-life/20-healthcare.md src/ko/us-life/`
  - SUMMARY: `- [병원과 의료보험 이해하기](./ko/us-life/20-healthcare.md)`
- [ ] **21** — `mv drafts/us-life/21-pharmacy.md src/ko/us-life/`
  - SUMMARY: `- [약국 이용하기 — 처방약 픽업, OTC](./ko/us-life/21-pharmacy.md)`
- [ ] **22** — `mv drafts/us-life/22-taxes.md src/ko/us-life/`
  - SUMMARY: `- [미국 세금 기초 — W-2, Tax Return](./ko/us-life/22-taxes.md)`
