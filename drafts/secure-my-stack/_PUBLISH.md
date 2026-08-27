# 발행 트래커 — 내 스택 안전하게 만들기 (시즌 3)

이 디렉터리(`drafts/secure-my-stack/`)의 글은 전부 **draft** 다. mdBook 은 `src/` 만 빌드하므로
여기 있는 글은 사이트에 뜨지 않는다(소스는 공개 repo 엔 보임).

**선행 시리즈 없음.** 앞선 두 시즌(Claude Code 내부 구조 / 멀티에이전트)과 독립된 주제다.

## 발행 방법 (한 편씩)

1. `mv drafts/secure-my-stack/<파일> src/ko/secure-my-stack/`
   (첫 발행이면 먼저 `mkdir -p src/ko/secure-my-stack`)
2. `src/SUMMARY.md` 의 `# 한국어` 섹션 아래에 해당 줄 추가.
   첫 발행 시 소제목 헤더 `# 내 스택 안전하게 만들기` 도 함께 추가.
3. 커밋 + push → GitHub Actions 가 빌드·배포.

**순서 주의:** 각 편이 "다음 편" 링크를 가지므로 순서대로 발행한다.

## 첫 발행 시 SUMMARY.md 에 추가할 소제목

```
# 내 스택 안전하게 만들기
```

## 읽기 순서와 발행 목록

- [ ] **00** — `mv drafts/secure-my-stack/00-four-doors.md src/ko/secure-my-stack/`
  - SUMMARY: `- [프롤로그 — 내 백엔드에는 문이 네 개다](./ko/secure-my-stack/00-four-doors.md)`
- [ ] **01** — `01-what-is-jwt.md`
  - SUMMARY: `- [JWT가 뭔가 — 생초보용](./ko/secure-my-stack/01-what-is-jwt.md)`
- [ ] **02** — `02-verify-jwt.md`
  - SUMMARY: `- [진짜 인증 경계 — Supabase JWT 검증하기](./ko/secure-my-stack/02-verify-jwt.md)`
- [ ] **03** — `03-webhook.md`
  - SUMMARY: `- [웹훅 문 — 잠글 수 없는 문 지키기](./ko/secure-my-stack/03-webhook.md)`
- [ ] **04** — `04-backdoor.md`
  - SUMMARY: `- [뒷문 — Cloud Run 직접 호출 막기](./ko/secure-my-stack/04-backdoor.md)`
- [ ] **05** — `05-long-connections.md`
  - SUMMARY: `- [긴 연결 문 — WebSocket과 MCP](./ko/secure-my-stack/05-long-connections.md)`
- [ ] **06** — `06-egress.md`
  - SUMMARY: `- [나가는 문 — Cloud Run에서 PlanetScale로](./ko/secure-my-stack/06-egress.md)`
- [ ] **07** — `07-token-storage.md`
  - SUMMARY: `- [토큰을 어디에 둘 것인가 — BFF와 쿠키](./ko/secure-my-stack/07-token-storage.md)`

## 시즌 구성 메모

- **범위 선언(0편):** 해결책을 **①엣지 · ②코드 · ③설정·콘솔** 세 갈래로 나누고,
  이 시리즈가 다루는 것은 **②와 ③**임을 명시했다. 체크리스트 57개 기준 ①은 3개뿐이다.
  **④ 탐지·대응(감사 로그·토큰 무효화·알림)은 범위 밖**이라고 0편에서 밝힌다.
  **"완벽한 보안"을 약속하지 않는다** — 대신 "문을 빠짐없이 세고, 닫히지 않는 것은
  닫히지 않는다고 말한다"가 약속이고, 그게 각 편 "확인 못 한 것" 섹션의 존재 이유다.
- **관통 명제:** "**Cloudflare 는 대체재가 아니라 앞에 세우는 층이다.**"
  많은 글이 "Cloudflare 붙이면 끝"이라고 하는데, `run.app` 뒷문이 열려 있으면 전부 무의미하다.
  진짜 인증 경계는 **NestJS** 이고, 그건 아무도 대신 해주지 않는다.
- **예시 스택(가공):** Next.js on Vercel(frontend + serverless BFF + edge)
  → NestJS on GCP Cloud Run(REST + WebSocket + MCP + 웹훅)
  → PlanetScale Postgres, Supabase 는 인증 전용(OAuth → JWT), RBAC 은 NestJS.
  **특정 서비스의 실제 구성이 아니라 글을 위해 세운 예시다.** 0편이 "이런 스택을 만들었다고
  해봅시다. 요즘 흔한 구성입니다"로 가정법을 걸어두었고, 본문도 "여러분 구조는 X다"가 아니라
  "이 구성에서는" 으로 서술한다. **이 톤을 깨지 말 것** — 일반 독자 대상 글이다.
- **비용 원칙:** 가능한 한 0원. 돈이 드는 항목(고정 egress IP + Cloud NAT)은 **6편에서 명시적으로 분리**했다.
- **눈높이:** Junior Software Engineer. 선행 지식 가정하지 않는다(그래서 1편이 JWT 생초보 설명).
- **증거 라벨:** `[관찰]` / `[문서]` / `[추론]`.

## 증거 라벨 현황

2026-08-27 에 **01~05 를 소급 검증**했다(06·07 은 집필 시점에 이미 적용).
라벨을 붙이는 작업이 아니라 **원문을 다시 대조하고 코드를 다시 돌리는** 작업으로 했고,
그 과정에서 실제로 틀린 것들이 나왔다:

- **04** — `--no-default-url` 이 Cloud Scheduler·Cloud Tasks·Eventarc·Pub/Sub·Workflows 를
  깨뜨린다는 공식 경고가 통째로 빠져 있었다.
- **01** — 디코드 예시 출력이 실제 출력과 달랐다(`app_metadata` 줄바꿈). 실행 결과로 교체.
- **05** — Access 무료 50 석은 공식 문서에서 확인이 안 돼 표현을 낮추고 "확인 못 한 것" 으로 내렸다.

| 편 | [관찰] | [문서] | [추론] | 확인 못 한 것 |
|---|---|---|---|---|
| 00 | 0 | 0 | 0 | 없음(프롤로그) |
| 01 | 1 | 0 | 0 | 있음 |
| 02 | 2 | 4 | 0 | 있음 |
| 03 | 3 | 2 | 0 | 있음 |
| 04 | 1 | 7 | 4 | 있음 |
| 05 | 1 | 6 | 2 | 있음 |
| 06 | 5 | 9 | 0 | 있음 |
| 07 | 4 | 10 | 0 | 있음 |

**00 은 소급하지 않았다.** 프롤로그라 개별 벤더 주장이 없고, 뒤 편들이 근거를 지고 있다.

원칙: **라벨을 채우려고 붙이지 않는다.** 원문 대조로 확인된 것만 `[문서]`,
직접 돌린 것만 `[관찰]`, 나머지는 `[추론]` 이거나 "확인 못 한 것" 으로 내린다.

## 각 편의 "반전"

| 편 | 반전 |
|---|---|
| 0 | Cloudflare Access 는 **사용자용이 아니라 팀용**이다. 그리고 `*.run.app` 이 열려 있다. |
| 1 | JWT 는 암호화가 아니라 **인코딩**이다. 누구나 읽을 수 있다. |
| 2 | Supabase 의 `role` 은 **Postgres 역할**이라 전원 동일하고, `user_metadata` 는 **클라이언트가 쓸 수 있다**. |
| 3 | 웹훅은 **로그인을 요구할 수 없는** 유일한 문이다. `@Public()` 과 `@UseGuards` 는 **한 쌍**이어야 한다. |
| 4 | Cloud Run 에서 `req.socket.remoteAddress` 는 **구글 내부 홉**이라 IP 검사가 전부를 막아버린다. |
| 5 | **전역 가드는 WebSocket 에 아예 돌지 않는다** — 핸드셰이크도 메시지도(실측). Access 도 `run.app` 우회는 못 막는다. |
| 6 | `sslmode=require` 는 **중간자를 못 막는다**(실측). Node `pg` 는 `psql` 과 다르고, **곧 더 약해진다**. |
| 7 | **캐시가 `Set-Cookie` 를 나눠주면 남의 계정으로 로그인된다.** 2편의 검증으로는 못 잡는다 — 토큰이 진짜라서. |

## 검증 자산

- `pglab/` — 자체 서명 인증서(CN=attacker-in-the-middle)를 쓰는 도커 Postgres 16.
  `sslmode` 4종 + Node `pg` 5종 비교. 6편의 [관찰] 근거.
- `jwtlab/` — `attack.mjs`(JWT 공격 5종), `webhook.mjs`, `origin.mjs`, `guard.mjs`. 2~4편 근거.
- `wslab/` — 실제 NestJS 앱으로 가드 실행 순서 실측. 5편 근거.
- `pglab/nodetest*.mjs` — Node `pg` 8.23.0 의 SSL 옵션 5종 비교(평문 여부 포함). 6편 근거.
- `cachelab/demo.mjs` — 앞단 캐시가 `Set-Cookie` 를 재사용해 **bob 이 alice 세션을 받는** 재현. 7편 근거.
- `sblab/` — `@supabase/auth-js` 2.112.4 소스에서 기본 저장소(localStorage) 확인. 7편 근거.

## 남은 작업

- [x] 7편 집필 (토큰 보관 — BFF와 쿠키)
- [x] 전편 상호 링크 점검 — 00→07 체인 정상
- [ ] 발행 전 `_PUBLISH.md` 와 검증 자산(`pglab/`, `cachelab/`, `sblab/`)은 **옮기지 않는다**

## 분량 (글자 수 기준, 한글은 바이트≠글자)

| 편 | 글자 |
|---|---|
| 00 | 4,996 |
| 01 | 9,882 |
| 02 | 9,576 |
| 03 | 9,005 |
| 04 | 9,000 |
| 05 | 9,599 |
| 06 | 10,163 |
| 07 | 7,205 |

06 이 가장 긴 이유: 시리즈에서 **유일하게 완전히 실행 가능한 실험**(도커 셋업 + 결과 + 정리)을 포함한다.
