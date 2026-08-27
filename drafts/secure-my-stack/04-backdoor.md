# 4편. 뒷문 — Cloud Run 직접 호출 막기

> 시리즈: 내 스택 안전하게 만들기
> 이 편에서 배우는 것: `*.run.app` 우회를 막는 **세 가지 방법**과 각각의 진짜 비용, 무료로 기본 URL을 끄는 법과 **순서 함정**, 그리고 3편의 IP 검사와 충돌하는 지점.

0편에서 이 그림을 봤습니다.

```
[정상] 공격자 → api.내도메인.com → Cloudflare(WAF) → Cloud Run
[우회] 공격자 → <서비스>-<번호>.<리전>.run.app → Cloud Run   ← 앞단을 안 거침
```

이번 편에서 닫습니다.

## 먼저 — 지금 열려 있는지 확인

```bash
gcloud run services describe <서비스> --region <리전> --format=yaml \
  | grep -E 'ingress|default-url|^  url'
```

> **출력이 비었다면?** 그게 흔한 경우입니다. `ingress` 를 명시적으로 설정한 적이 없으면 애노테이션 자체가 없어서 아무 줄도 안 나옵니다. **즉 `ingress` 줄이 안 보이면 기본값 `all` 이고, 뒷문이 열려 있다는 뜻입니다.** `default-url` 줄이 없는 것도 마찬가지로 "끈 적 없음"입니다.
>
> 애노테이션 경로를 직접 지정하는 `--format="value(...)"` 형태는 버전에 따라 위치가 달라 역시 빈 값이 나오기 쉬우니, yaml 로 뽑아 보는 편이 낫습니다.

`ingress` 값의 의미입니다. [문서]

| 값 | 무엇을 허용 |
|---|---|
| `all` (기본) | **인터넷에서 `run.app` URL 로 직접** 오는 요청 포함 전부 |
| `internal-and-cloud-load-balancing` | 내부 + 외부 로드밸런서 |
| `internal` | 내부만 |

**`all` 이면 뒷문이 열려 있습니다.**

> **손잡이가 둘이라는 걸 먼저 짚어둡니다.** `ingress` 는 **어떤 경로로 들어올 수 있나**를 정하고, `--no-default-url` 은 **`run.app` 이라는 주소를 없앱니다.** B 를 해도 `ingress` 값은 `all` 그대로입니다 — 주소가 사라졌을 뿐이죠. C 는 `ingress` 쪽을 조입니다.

## 세 가지 방법

| | A. Cloudflare + 앱 검증 | B. 기본 URL 끄기 | C. GCLB + Cloud Armor |
|---|---|---|---|
| `run.app` | **열림.** 앱이 걸러냄 | **꺼짐** | 꺼짐 |
| 막는 위치 | 내 코드 | **플랫폼** | 플랫폼 |
| 월 고정비 | 없음 | 없음~ | 로드밸런서 + 정책 |
| WAF·레이트리밋 | Cloudflare | **없음** | Cloud Armor |
| 설정 난이도 | 낮음 | 중간 | 높음 |

**B의 "없음~"에 물결표를 붙인 이유**는 아래에서 설명합니다. 그리고 A 행의 "열림"은 **출발 상태**를 뜻합니다 — A 를 B 와 함께 쓰면 주소는 닫히고 시크릿 검증만 남습니다.

## B. 기본 URL 끄기 — 가장 확실하고 대체로 무료

Cloud Run 은 기본 URL 자체를 끌 수 있습니다.

```bash
gcloud run services update <서비스> --region <리전> --no-default-url
```

`gcloud run services update --help` 의 원문입니다. (Google Cloud SDK 564.0.0) [관찰]

```
--[no-]default-url
   Toggles the default url for a run service. This is enabled by default
   if not specified. Use --default-url to enable and --no-default-url to disable.
```

끄고 나면 남는 입구는 **로드밸런서**와 **도메인 매핑** 뿐입니다.

> **리비전 태그 URL 을 쓰신다면 따로 확인하세요.** `green---myservice-xxxx.a.run.app` 같은 주소도 `run.app` 이지만, 이 플래그가 그것까지 끄는지는 문서에서 못 찾았습니다. 끈 뒤에 태그 URL 로 직접 요청해보는 게 확실합니다.

### 🚨 순서를 지키세요

공식 문서가 명시합니다. [문서]

> *"To use custom domain mappings, map the custom domain before you disable the `run.app` URL."*

**커스텀 도메인을 먼저 연결하고, 그다음에 기본 URL을 끄세요.** 순서를 바꾸면 **들어갈 문이 하나도 없는 상태**가 됩니다.

복구는 `--default-url` 한 줄이면 되지만, **그때까지는 전면 장애**입니다. 그리고 3편에서 `run.app` 주소로 웹훅을 등록해뒀다면 **그 웹훅도 같이 죽습니다** — `setWebhook` 을 커스텀 도메인으로 다시 걸어주세요.

> **🚨 같이 죽는 게 웹훅만이 아닙니다.** 공식 문서가 경고합니다. [문서]
>
> *"Before you disable the default URL, be aware that the following Google Cloud services or instance use the default `run.app` URL to invoke Cloud Run. Disabling the default `run.app` URL prevents these services or instance from working as expected"*
>
> 목록에 **Cloud Scheduler, Cloud Tasks, Eventarc, Pub/Sub, Workflows** 가 있습니다. 배치 작업이나 이벤트 연동을 붙여뒀다면 **끄기 전에 먼저 확인하세요.**

### 물결표의 정체

커스텀 도메인을 붙이는 방법이 둘인데 비용이 다릅니다.

| | Cloud Run 도메인 매핑 | 외부 Application Load Balancer |
|---|---|---|
| 비용 | 없음 | 발생 |
| 가용성 | **10 개 리전** | 전 리전 |
| 상태 | **Preview** | GA |
| 구글 권장 | — | **이쪽** |

도메인 매핑이 되는 리전은 이게 전부입니다. [문서]

```
asia-east1, asia-northeast1, asia-southeast1, europe-north1, europe-west1,
europe-west4, us-central1, us-east1, us-east4, us-west1
```

그리고 공식 문서의 경고가 생각보다 셉니다. [문서]

> *"Cloud Run domain mappings are in the preview launch stage. Due to latency issues, they are **not production-ready** and are not supported at General Availability."*

> **그래서 "무료로 뒷문을 닫는다"는 말은 조건부입니다.** 리전이 맞고 Preview 상태를 감수할 수 있으면 참입니다. **프로덕션이라면 구글 스스로 권하지 않으므로**, 결국 로드밸런서 비용을 놓고 판단하게 됩니다. 먼저 이 표부터 확인하세요.

## A. Cloudflare 앞단 + 앱 검증 — 가장 손쉬운 길

기본 URL을 못 끄거나, WAF·레이트리밋이 지금 필요하다면 이쪽입니다.

### 그전에 — Cloudflare 는 Cloud Run 에 어떻게 닿나

여기서 한 가지 짚고 가야 합니다. `api.내도메인.com` 을 `xxx.run.app` 으로 CNAME 만 걸어서는 **안 됩니다.** Google 프론트엔드가 `api.내도메인.com` 이라는 호스트를 모르기 때문입니다.

**A 를 하려면 커스텀 도메인 연결이 먼저입니다** — B 에서 쓸 도메인 매핑이든 로드밸런서든요. 즉 **A 와 B 는 대립하는 선택지가 아니라 같은 기반 위에 얹는 것**입니다.

### 무엇으로 걸러내나

**비밀 헤더 하나입니다.** Cloudflare 쪽 Transform Rule 로 헤더를 추가하고, 서버가 그것만 확인합니다.

> **IP 대역 검사는 넣지 않았습니다.** 세 가지 이유입니다.
>
> **① 안 됩니다.** TLS 를 Google 프론트엔드가 종단해서, 컨테이너가 보는 소켓 상대방은 **Google 내부 홉**이지 Cloudflare 가 아닙니다. 그대로 두면 **모든 요청이 403** 입니다. [추론]
> **② 우회로도 취약합니다.** `X-Forwarded-For` 는 앞에서 읽으면 위조 가능하고(3편의 `trust proxy` 함정), 뒤에서 읽으려면 홉 수를 알아야 해서 앞단이 바뀔 때마다 깨집니다.
> **③ 필요가 없습니다.** Cloudflare 대역은 **모든 고객이 공유**하므로 [추론], 헤더가 샜다면 공격자도 그 대역에서 보낼 수 있습니다. **시크릿 하나면 충분하고, 시크릿이 새면 IP 도 못 막습니다.**

```ts
// origin.guard.ts
import { CanActivate, ExecutionContext, Injectable, ForbiddenException } from '@nestjs/common'
import { timingSafeEqual } from 'node:crypto'

// 교체 중에는 둘 다 받는다 (아래 '무중단 교체' 참고)
const SECRETS = [process.env.ORIGIN_SECRET, process.env.ORIGIN_SECRET_NEXT]
  .filter((v): v is string => !!v)

function secretOk(got: unknown): boolean {
  if (typeof got !== 'string') return false
  const a = Buffer.from(got)
  return SECRETS.some(s => {
    const b = Buffer.from(s)
    return a.length === b.length && timingSafeEqual(a, b)
  })
}

@Injectable()
export class OriginGuard implements CanActivate {
  canActivate(ctx: ExecutionContext): boolean {
    const req = ctx.switchToHttp().getRequest()
    if (!secretOk(req.headers['x-origin-secret'])) throw new ForbiddenException()
    return true
  }
}
```

### 어디에 거나

전역에 겁니다. 2편의 JWT 가드보다 **바깥**이어야 합니다 — 신원 확인 전에 "이 요청이 우리 앞단을 거쳤나"부터 보는 게 순서니까요.

```ts
import { APP_GUARD } from '@nestjs/core'

providers: [
  { provide: APP_GUARD, useClass: OriginGuard },        // ← 먼저
  { provide: APP_GUARD, useClass: SupabaseAuthGuard },  // ← 그다음
]
```

> **등록 순서가 곧 실행 순서입니다.** 배열 순서를 바꾸면 실행 순서도 바뀝니다.

**웹훅도 이 가드를 통과해야 합니다.** 텔레그램 → Cloudflare → Cloud Run 이므로 Transform Rule 이 **웹훅 경로에도 헤더를 붙이는지** 확인하세요. 3편의 `@Public()` 은 **JWT 가드만** 비켜가게 하지 이 가드는 비켜가지 않습니다 — 그게 맞습니다.

> **한 가지 주의**: HTTP 시작·활성 프로브나 외부 업타임 체크는 Cloudflare 를 안 거치므로 **403** 이 됩니다. 프로브를 TCP 로 두거나 경로를 예외 처리하세요.

### 3편과 충돌하는 지점

```
텔레그램 → Cloudflare → Cloud Run
              ↑ 여기서 발신 IP 가 바뀐다
```

**Cloudflare 를 앞에 두면 텔레그램 웹훅도 Cloudflare 를 거쳐 옵니다.** 그러니 3편의 텔레그램 IP 검사(`CHECK_IP`)는 **꺼두세요.** 3편에서 예고한 그대로입니다.

> 정보가 사라지는 건 아닙니다. *"CF-Connecting-IP provides the client IP address connecting to Cloudflare to the origin web server."* [문서] 정말 필요하면 그 값으로 검사할 수 있습니다. 다만 **시크릿이 이미 1 차 방어이므로 대개 불필요**합니다.

**결론: IP 대역 검사는 이 스택에서 빼는 게 낫습니다.** 시크릿 헤더 하나로 3편·4편이 모두 정리됩니다.

### 시크릿 무중단 교체

위 코드가 시크릿을 **배열로** 받는 이유입니다.

```
① ORIGIN_SECRET_NEXT 에 새 값 배포   → 서버가 둘 다 받음
② Cloudflare Transform Rule 을 새 값으로 변경
③ ORIGIN_SECRET 을 새 값으로, NEXT 제거
```

한 값만 쓰면 ②와 ③ 사이에 **전면 403** 이 납니다.

### 앞단을 우회하면

Cloudflare 프록시를 끄면(회색 구름) 헤더가 안 붙어서 **모든 요청이 403** 이 됩니다. DNS 를 만질 때 이걸 기억하세요.

> **`ORIGIN_SECRET` 을 비우는 건 해결책이 아닙니다.** 위 코드는 값이 없으면 `SECRETS` 가 빈 배열이 되고, `[].some()` 은 `false` 라 **여전히 전부 403** 입니다. (기본값이 "막힘"이라는 점에서 이 동작 자체는 옳습니다.)
>
> 정말 비상 스위치가 필요하면 **별도 플래그**로 두세요.
>
> ```ts
> if (process.env.ORIGIN_GUARD_DISABLED === 'true') return true
> ```
>
> 다만 켜는 순간 **뒷문이 열립니다.** 켜둔 채로 잊지 마세요.

### A의 한계

**뒷문으로 온 요청도 일단 Cloud Run 을 깨웁니다.** 거부하더라도 인스턴스가 뜨고 CPU 를 씁니다. [추론] 평상시엔 무시할 만하지만, **대량 공격이면 그 자체가 비용**입니다.

그때가 B나 C로 옮길 시점입니다.

## C. GCLB + Cloud Armor — 언제 값어치를 하나

누군가 Cloud Armor 를 권했다면, **그 값어치는 "문을 닫는 것"이 아닙니다.** 문 닫기는 B가 무료로 합니다.

Cloud Armor 가 주는 것은 **관리형 WAF 룰과 레이트리밋**입니다. Cloudflare 가 주는 것과 같은 범주죠. 그래서 선택은 이렇게 갈립니다.

| 이미 쓰는 것 | 권장 |
|---|---|
| Cloudflare 를 쓰고 있다 | **A + B** — 주소는 B 로 닫고, WAF 와 원본 검증은 Cloudflare 로 |
| GCP 로 통일하고 싶다 | **C** |
| 둘 다 필요 없다 | **B만** |

**Cloud Armor 는 GCLB 를 필요로 하고, 그게 비용의 대부분**입니다. 문서가 명시합니다 — *"Cloud Armor also protects serverless NEGs when traffic is routed through a load balancer."* [문서] Cloud Run 앞에 붙이려면 서버리스 NEG → 백엔드 서비스 → 로드밸런서 → 인증서 → 보안 정책 순으로 만들어야 합니다.

### 어떻게 막는 건가

**Cloud Armor 는 별도의 장비가 아닙니다.** 로드밸런서의 백엔드 서비스에 붙이는 **정책**이고, 평가는 로드밸런서 경로 안에서 끝납니다. 홉이 하나 더 생기는 게 아닙니다.

```
요청 → [ Google 엣지 : 로드밸런서 + Cloud Armor 정책 ] → 서버리스 NEG → Cloud Run
              └ 여기서 판정이 끝남 (백엔드에 닿기 전)
```

문서 표현으로는 *"at the Google Cloud edge, as close as possible to the source of incoming traffic"* 에서 평가합니다. [문서] **거부된 요청은 Cloud Run 을 깨우지도 않습니다** — 바로 위 "A의 한계"에서 지적한 문제를 C 는 구조적으로 피합니다.

판정 방식은 **우선순위 규칙 목록**입니다. 규칙 하나가 **매치 조건 + 액션**이고, 번호가 작을수록 먼저 평가되며 **먼저 맞는 하나가 이깁니다.** 액션은 allow / deny(403·404·502) / redirect / throttle / rate-based ban 입니다. WAF 룰은 직접 짜는 게 아니라 **OWASP Core Rule Set** 기반의 사전 구성 룰을 켜는 것이고요. [문서]

> **그런데 Cloud Armor 가 문을 닫는 게 아닙니다.** C 행의 "`run.app` 꺼짐"은 Cloud Armor 덕이 아니라 **`ingress` 설정** 덕입니다. `run.app` 으로 직접 온 요청은 로드밸런서를 안 지나므로 **Cloud Armor 가 평가할 기회조차 없습니다.** 0편에서 한 말이 여기에도 그대로 적용됩니다 — **앞단은 층이지 대체재가 아닙니다.**

### 🚨 C 로 가면 텔레그램 웹훅이 깨집니다

3편에서 등록한 웹훅이 그대로 살아 있을 거라 생각하기 쉬운데, **세 군데가 동시에 걸립니다.**

**① 웹훅 URL 을 다시 등록해야 합니다.** `ingress` 를 잠그는 순간 `run.app` 으로 오던 호출이 즉시 죽습니다. **로드밸런서와 인증서를 먼저 세우고 → 웹훅을 옮기고 → 그다음에 `ingress` 를 잠그세요.** B 의 순서 함정과 같습니다.

```bash
curl -X POST "https://api.telegram.org/bot<봇토큰>/setWebhook" \
  -d "url=https://api.내도메인.com/webhook/<랜덤>" \
  -d "secret_token=$SECRET"
```

**② 포트를 맞추세요.** 3편에서 인용한 문서에 *"on port 443, 80, 88, or 8443"* 이 있습니다. 로드밸런서를 **443** 에 세우면 됩니다.

**③ 그리고 이게 진짜 함정입니다 — WAF 오탐.**

Cloud Armor 의 사전 구성 WAF 룰은 **요청 바디를 검사합니다.** 기본 **64KB** 까지 보고 JSON 파싱도 켤 수 있습니다. [문서]

그런데 텔레그램 웹훅 바디에 들어오는 게 무엇입니까? **사용자가 봇에게 보낸 아무 텍스트**입니다.

```json
{ "message": { "text": "select * from users where 1=1 -- 이거 왜 안돼?" } }
```

사용자가 SQL 질문을 하거나 `<script>` 를 언급하거나 코드 조각을 붙여넣으면 **OWASP 시그니처에 걸립니다.** 공격이 아닌데 차단되고, 텔레그램 쪽에서는 그냥 "서버가 에러를 준다"로만 보입니다. **개발 관련 봇이라면 거의 확실히 터집니다.**

대응은 **웹훅 경로만 WAF 앞에서 빼는 것**입니다. 낮은 번호(먼저 평가)에 allow 규칙을 두면 아래 WAF 룰까지 안 내려갑니다.

```
우선순위 1000 : 경로가 /webhook/<랜덤> 이면 → allow   ← 여기서 끝
우선순위 2000 : 사전 구성 WAF 룰            → deny
```

**WAF 를 껐는데 괜찮냐고요?** 괜찮습니다. **그 경로는 원래 시크릿 헤더가 지킵니다**(3편). 진짜 텔레그램인지는 `X-Telegram-Bot-Api-Secret-Token` 만 알고, WAF 는 웹훅에 대해 방어는 거의 못 하면서 오탐만 만듭니다.

**그대로 유지되는 것**: `secret_token` 헤더는 로드밸런서를 그대로 통과하므로 **3편 가드는 손댈 필요 없습니다.**

**반대로 A 와 충돌하는 것**: Cloudflare 를 걷어내고 C 로 가면 **`OriginGuard` 가 전부 403** 을 냅니다. 시크릿 헤더를 붙여주던 게 Cloudflare Transform Rule 이었으니까요. **A 를 끄든지, 헤더를 붙일 주체를 새로 만들든지 정해야 합니다.**

바꾼 뒤에는 `getWebhookInfo` 의 `last_error_message` 를 확인하세요. WAF 오탐이면 거기서 드러납니다.

## 그래서 무엇을 고를까

```
커스텀 도메인을 어떻게 붙일 것인가?      ← 이게 먼저입니다
   ├─ 도메인 매핑 (리전 O, Preview 감수)
   │     → 무료. 그 위에 A(시크릿 검증)를 얹고, 원하면 B로 기본 URL 도 끈다
   └─ 로드밸런서 (프로덕션 권장)
         ├─ WAF 를 Cloudflare 로  → A + B
         └─ WAF 를 GCP 로         → C (Cloud Armor)
```

**A 는 독립된 선택지가 아닙니다.** 위에서 봤듯 Cloudflare 가 Cloud Run 에 닿으려면 도메인 연결이 먼저이므로, **A 는 어느 쪽을 고르든 그 위에 얹는 층**입니다.

**가장 흔한 정답은 도메인을 붙이고 → A 를 켜고 → B 를 더하는 것**입니다.

> **"옮긴다"가 아니라 "더한다"입니다.** B 로 기본 URL 을 꺼도, 도메인 매핑된 주소는 Google 프론트엔드에서 여전히 응답합니다. **Cloudflare 를 건너뛰고 그쪽으로 직접 요청하면 WAF 를 우회**할 수 있죠. [추론] **Cloudflare 가 WAF 역할을 하는 한 A 의 시크릿 검증은 계속 켜두세요.**

## 체크리스트

- [ ] `gcloud run services describe` 로 **현재 `ingress` 값을 확인**했다
- [ ] (B) **커스텀 도메인을 먼저 연결**하고 그다음에 `--no-default-url` 했다
- [ ] (A) 시크릿 헤더를 **`timingSafeEqual` 로** 비교한다
- [ ] (A) `OriginGuard` 가 **JWT 가드보다 먼저** 걸려 있다
- [ ] (A) Transform Rule 이 **웹훅 경로에도** 헤더를 붙인다
- [ ] (A) HTTP 프로브·업타임 체크가 **403 나지 않게** 처리했다
- [ ] **3편의 `CHECK_IP` 를 껐다** (Cloudflare 를 앞에 뒀다면)
- [ ] 시크릿 **무중단 교체 절차**를 알고 있다 (두 값 동시 허용)
- [ ] B 를 했다면 `setWebhook` 이 **커스텀 도메인**을 가리킨다
- [ ] (C) 로드밸런서를 세운 뒤 **웹훅을 먼저 옮기고** `ingress` 를 잠갔다
- [ ] (C) **웹훅 경로가 WAF 룰보다 먼저 allow** 된다 (사용자 메시지가 시그니처에 걸린다)

## 확인 못 한 것

- **리비전 태그 URL**(`green---myservice-xxxx.a.run.app`)도 `--no-default-url` 로 같이 꺼지는지. 문서에서 못 찾았습니다. 끈 뒤 직접 요청해보세요.
- **Cloud Run 의 소켓 상대방이 Google 내부 홉**이라는 것. TLS 종단 구조상 그렇게 되지만, 실제 Cloud Run 에 배포해서 확인하지는 못했습니다.
- **도메인 매핑 주소가 `--no-default-url` 이후에도 응답한다**는 것. 손잡이가 다르니 그래야 맞지만, 직접 확인 못 했습니다.
- **도메인 매핑 리전 목록과 Preview 상태**는 자주 바뀝니다. 쓰기 직전에 다시 확인하세요.
- 위 `gcloud` 도움말은 **Google Cloud SDK 564.0.0** 기준입니다.

---

## 정리

- 뒷문 닫는 법은 **셋**이고, **문 닫기 자체는 무료로 가능**합니다(`--no-default-url`).
- **순서가 중요합니다** — 도메인을 먼저 연결하고 기본 URL을 끄세요.
- 다만 **도메인 매핑이 Preview·제한적**이라, 안 되는 환경이면 로드밸런서 비용이 붙습니다.
- **Cloud Armor 의 값어치는 문 닫기가 아니라 WAF** 입니다. Cloudflare 와 같은 범주입니다.
- **IP 대역 검사는 이 스택에서 빼세요.** Cloud Run 은 TLS 를 Google 이 종단해서 소켓 상대방이 Cloudflare 가 아니고, `X-Forwarded-For` 파싱은 앞단 구성이 바뀔 때마다 깨집니다. **시크릿 헤더 하나면 충분합니다.**
- **A 는 B 로 "옮기는" 게 아니라 "더하는" 것**입니다. 도메인 매핑된 주소는 B 이후에도 직접 닿으므로, Cloudflare 가 WAF 라면 시크릿 검증을 유지하세요.

다음 편은 **긴 연결**입니다. 브라우저 WebSocket 이 헤더를 못 붙이는 제약, 지금까지 쌓은 전역 가드가 WS 에는 돌지 않는다는 사실, 그리고 admin 전용 MCP 를 Access 로 막을 때 빠지기 쉬운 함정.

> 이전 편: [3편. 웹훅 문 — 잠글 수 없는 문 지키기](./03-webhook.md)
> 다음 편: [5편. 긴 연결 문 — WebSocket과 MCP](./05-long-connections.md)
