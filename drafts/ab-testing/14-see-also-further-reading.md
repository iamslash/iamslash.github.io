# See Also — 더 공부할 거리 (쉬운 것부터)

이 시리즈(0~13편)는 A/B 테스트 통계의 **밑바닥 직관**을 다뤘습니다. 여기서 더 나아가고 싶은 분을 위해, **쉬운 것부터 어려운 순서로** 공부 재료를 정리했습니다. 대부분 **무료(웹/PDF)** 이고, 유료는 표시했습니다.

> **어디까지 하면 되나:** **0~1단계면 실무 충분**, **2단계면 상급자**, **3~4단계는 그 상황이 실제로 닥쳤을 때만** 파도 됩니다.

## 0단계 · 통계 감각 잡기 🟢 (가장 쉬움)

- **이 시리즈(0~13편)** — 밑바닥 직관. 출발점.
- **StatQuest** (YouTube, Josh Starmer) — 통계 개념을 그림으로 풀어주는 최고의 입문 채널. 무료.
- **Google "A/B Testing" 코스** (Udacity) — 실무 흐름을 감으로 익히기. 무료.
- **《Statistics Done Wrong》** (Alex Reinhart) — 얇고 재밌는 "통계 함정 모음". 무료 웹판 있음.

## 1단계 · A/B 실전 입문 🟢🟡

- **"How Not To Run an A/B Test"** (Evan Miller, 블로그) — peeking(훔쳐보기)을 머리에 각인시키는 명문. 무료. (우리 8편과 짝)
- **회사 실험 블로그** — Microsoft ExP · Netflix · Airbnb · Booking · Spotify · DoorDash 엔지니어링 블로그. 실전 사례의 보고. 무료.
- **《Trustworthy Online Controlled Experiments》** (Kohavi·Tang·Xu, 2020) — 이 분야의 **사실상 표준서**. 넷플릭스·MS·구글의 노하우를 한 권에. 유료. *이 시리즈가 이 책의 "쉬운 입문" 버전에 가깝습니다.*

## 2단계 · 인과추론 기초 🟡

- **《Causal Inference for the Brave and True》** (Matheus Facure) — 코드로 배우는 인과추론, 아주 친절. **무료 온라인.**
- **《Causal Inference: The Mixtape》** (Scott Cunningham) — 계량경제 관점(이중차분·synthetic control·회귀불연속·도구변수). **무료.**
- 핵심 개념: 잠재적 결과(Rubin), 교란(confounding), SUTVA — A/B가 왜 "가장 깨끗한 인과추론"인지 알게 됩니다.

## 3단계 · 고급 · 프론티어 🔴

- **CUPED 원논문** (Deng·Xu·Kohavi, 2013) — 10편에서 재현한 분산감소.
- **"Graph Cluster Randomization"** (Ugander et al., 2013) — 간섭·네트워크 실험(13편 부록의 학문판).
- **순차검정 · anytime-valid** — Howard·Ramdas·Waudby-Smith 계열(신뢰수열). 8편의 이론적 뿌리.
- **Synthetic Control** (Abadie) · **Meta GeoLift** — geo/market 실험(13편 부록의 분석 도구).
- **《Bandit Algorithms》** (Lattimore·Szepesvári) — 밴딧의 정석. **무료 PDF.** (12편의 심화)
- **이질적 효과(HTE)** — "누구에게 먹히나"를 재는 causal forest(Wager·Athey), Microsoft **EconML**.

## 4단계 · 이론 심화 🔴🔴 (가장 어려움)

- **《Causal Inference: What If》** (Hernán·Robins) — 인과추론 엄밀 정석. **무료 PDF.**
- **《Causal Inference for Statistics, Social, and Biomedical Sciences》** (Imbens·Rubin) — 두꺼운 표준 교과서. 유료.

---

## 공부 순서에 대한 한마디

새 기법을 많이 아는 것보다 **두 가지가 훨씬 중요합니다.**

1. **지표(OEC) 설계** — 무엇을 측정할지. 실험을 망치는 1위는 어려운 수학이 아니라 **잘못된 지표 선택**입니다.
2. **신뢰성 있는 실행** — SRM 확인, peeking 금지, 오염 차단. (Twyman's law: "너무 좋아 보이는 결과는 대개 뭔가 틀린 것이다.")

화려한 기법(밴딧·synthetic control·HTE)은 **특정 상황용 20%** 이고, 실전 가치의 **80%는 "옳은 지표 + 믿을 수 있는 실행"** 에서 나옵니다. 프론티어(간섭·이질효과·준실험)는 **"이건 유저 A/B로 하면 안 되겠다"라고 알아차리는 것**만으로 대부분 해결됩니다 — 나머지는 그때 파면 됩니다.

---
← 이전: [부록. 유저 단위가 깨질 때 — 간섭과 Pair Market Test](./13-geo-pair-market-test.md)
