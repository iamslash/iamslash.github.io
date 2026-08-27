# 3편. 웹훅 문 — 잠글 수 없는 문 지키기

> 시리즈: 내 스택 안전하게 만들기
> 이 편에서 배우는 것: 왜 이 문만 로그인을 요구할 수 없는지, 텔레그램이 진짜인지 확인하는 법, 그리고 **가드에서 빼기만 하면 그게 곧 구멍**이라는 것.

2편 체크리스트의 마지막 줄을 기억하시나요?

> - [ ] 웹훅 경로는 이 가드에서 제외돼 있다 — 단 **제외한 경로는 3편의 시크릿 검증이 대신 지켜야 합니다. 검증 없이 열어두면 그냥 구멍입니다.**

이번 편이 그 숙제입니다.

## 왜 이 문만 다른가

0편에서 문을 넷 셌습니다. 앞의 셋은 **내 사용자**나 **내가 허락한 클라이언트**라 로그인을 요구할 수 있습니다.

**텔레그램은 아닙니다.**

```
텔레그램 서버 ──POST──> https://api.내도메인.com/webhook/telegram
     ↑
  내 로그인 화면을 본 적 없음. Supabase 계정도 없음. JWT 도 없음.
```

그리고 **때리게 놔둬야 합니다.** 막으면 봇이 동작을 안 하니까요.

> **그래서 이 문은 "누구인가"가 아니라 "무엇을 아는가"로 지킵니다.** 신원 대신 **공유 비밀**을 확인합니다.

## 1단계 — 시크릿 토큰

텔레그램은 웹훅을 등록할 때 비밀 문자열을 함께 줄 수 있습니다. 그러면 **매 요청 헤더에 그걸 실어 보냅니다.**

공식 문서의 `setWebhook` 설명입니다. [문서]

```
secret_token
  A secret token to be sent in a header 'X-Telegram-Bot-Api-Secret-Token'
  in every webhook request, 1-256 characters.
  Only characters A-Z, a-z, 0-9, _ and - are allowed.
  The header is useful to ensure that the request comes from a webhook set by you.
```

마지막 줄이 이 편의 요지를 텔레그램 스스로 적어둔 것입니다 — **"당신이 설정한 웹훅에서 온 요청인지 확인하는 용도."**

등록은 이렇게 합니다.

```bash
# ① 먼저 만들어서 어딘가에 저장하고
SECRET=$(openssl rand -hex 32)
echo "$SECRET"          # ← Secret Manager 나 환경변수로 옮겨두세요

# ② 그다음 등록
curl -X POST "https://api.telegram.org/bot<봇토큰>/setWebhook" \
  -d "url=https://api.내도메인.com/webhook/telegram" \
  -d "secret_token=$SECRET"
```

> **파이프로 바로 넘기지 마세요.** `secret_token=$(openssl rand -hex 32)` 를 한 줄로 쓰면 **텔레그램만 알고 여러분은 모르는 값**이 됩니다. 서버가 검증할 수 없죠.

> `secret_token`에 쓸 수 있는 글자가 정해져 있습니다. `openssl rand -hex` 는 16진수만 내므로 안전합니다. `base64` 는 `+`·`/`가 섞여서 거부될 수 있습니다.

## 2단계 — 발신 IP 대역

텔레그램은 정해진 대역에서만 보냅니다. 공식 문서 원문입니다. [문서]

```
Accepts incoming POSTs from subnets 149.154.160.0/20 and 91.108.4.0/22
on port 443, 80, 88, or 8443.
```

같은 문서가 이렇게 덧붙입니다.

```
Our IP-range might change in the future.
```

같은 문서에 **`Supports IPv4, IPv6 is currently not supported for webhooks.`** 도 있습니다. 아래 코드가 `'ipv4'` 로만 검사하는 근거입니다.

**그래서 IP만으로 지키면 안 됩니다.** 대역이 바뀌면 봇이 조용히 죽습니다. **시크릿이 1차 방어, IP는 보조**입니다.

## 검증 코드

```ts
// telegram-webhook.guard.ts
import { CanActivate, ExecutionContext, Injectable, ForbiddenException } from '@nestjs/common'
import { timingSafeEqual } from 'node:crypto'
import { BlockList, isIPv4 } from 'node:net'

const SECRET = process.env.TELEGRAM_WEBHOOK_SECRET!
// IP 검사는 기본 꺼둠 — 아래 '켜기 전에 확인하세요' 참고
const CHECK_IP = process.env.TELEGRAM_CHECK_IP === 'true'

// 텔레그램 발신 대역 (공식 문서 — 바뀔 수 있음)
const telegramNet = new BlockList()
telegramNet.addSubnet('149.154.160.0', 20, 'ipv4')
telegramNet.addSubnet('91.108.4.0', 22, 'ipv4')

function secretOk(got: unknown): boolean {
  if (typeof got !== 'string') return false
  const a = Buffer.from(got), b = Buffer.from(SECRET)
  // 길이가 다르면 timingSafeEqual 이 예외를 던진다 → 먼저 거른다
  return a.length === b.length && timingSafeEqual(a, b)
}

// ★ Node 가 :: 로 듣고 있으면 IP 가 '::ffff:1.2.3.4' 로 들어온다
function fromTelegram(ip: unknown): boolean {
  if (typeof ip !== 'string') return false
  const v4 = ip.startsWith('::ffff:') ? ip.slice(7) : ip
  return isIPv4(v4) ? telegramNet.check(v4, 'ipv4') : false
}

@Injectable()
export class TelegramWebhookGuard implements CanActivate {
  canActivate(ctx: ExecutionContext): boolean {
    const req = ctx.switchToHttp().getRequest()

    if (!secretOk(req.headers['x-telegram-bot-api-secret-token'])) {
      throw new ForbiddenException()
    }
    // IP 검사는 선택 — 아래 주의사항을 읽고 켜세요
    if (CHECK_IP && !fromTelegram(req.ip)) {
      throw new ForbiddenException()
    }
    return true
  }
}
```

두 가지를 짚습니다.

**`timingSafeEqual`을 쓴 이유.** 보통의 `===` 는 첫 글자가 다르면 바로 끝납니다. 그 미세한 시간 차이로 시크릿을 한 글자씩 알아내는 공격이 있습니다. 이건 항상 같은 시간을 씁니다. **다만 길이가 다르면 예외를 던지므로** 길이를 먼저 비교해야 합니다. (그 비교가 길이는 노출하지만, 무작위 64 글자에서는 문제가 안 됩니다.)

**가드는 바디 파싱 뒤에 돕니다.** NestJS 순서가 미들웨어 → 가드 → 컨트롤러라, 시크릿 검증 전에 이미 본문이 파싱됩니다. 다행히 Express 의 JSON 파서는 기본 상한이 100KB 라 무한정 먹지는 않습니다. (Express 5.2.1 로 확인 — 150KB 를 보내면 **413** 이 떨어집니다.) [관찰] 상한을 늘려두셨다면 웹훅 경로만은 되돌리는 게 안전합니다.

**`::ffff:` 를 벗기는 이유.** Node 가 IPv6 소켓(`::`)으로 듣고 있으면 IPv4 접속도 `::ffff:149.154.167.41` 형태로 들어옵니다. 직접 돌려본 결과입니다. [관찰]

```
149.154.167.41          check(...,'ipv4') = true
::ffff:149.154.167.41   check(...,'ipv4') = false   ← 정상 트래픽인데 막힘
→ ::ffff: 를 벗긴 뒤              = true
```

그대로 넣으면 **정상 텔레그램 트래픽이 전부 막힙니다.** 위에서 경고한 "봇이 조용히 죽는" 상황이 자기 코드에서 나는 셈이죠.

### IP 검사는 켜기 전에 확인하세요

`CHECK_IP` 를 기본값으로 두지 않은 이유가 있습니다. **`req.ip` 가 진짜 발신 IP 라는 보장이 없습니다.**

앞에 무언가(Cloudflare, 로드밸런서, Cloud Run 자체)가 있으면 `req.ip` 는 **그 프록시의 IP** 이거나, `X-Forwarded-For` 를 어떻게 해석하느냐에 따라 달라집니다.

> **`app.set('trust proxy', true)` 를 그냥 켜지 마세요.** 그러면 `req.ip` 가 `X-Forwarded-For` 의 **맨 앞 값**이 되는데, 그 값은 **클라이언트가 마음대로 넣을 수 있습니다.** 방금 막으려던 위조를 오히려 열어주는 셈입니다.

**켜기 전에 한 번만 실측하세요.**

```ts
// 진짜 요청 한 번을 받아 로그로 확인
console.log({ ip: req.ip, xff: req.headers['x-forwarded-for'] })
```

텔레그램 대역이 보이면 켜고, 프록시 IP 만 보이면 **끄고 시크릿만 믿으세요.** 시크릿이 1 차 방어라고 한 이유입니다.

> **4편 예고:** 뒷문을 닫으면서 Cloudflare 를 앞에 두면 `req.ip` 는 Cloudflare 의 IP 가 됩니다. 그 구성에서는 **IP 검사를 꺼야** 합니다.

## 정말 막히는지 확인

아래 로직을 떼어내 직접 돌려봤습니다. [관찰]

```js
// webhook.mjs — 위 로직만 떼어내 테스트
import { timingSafeEqual } from 'node:crypto'
import { BlockList } from 'node:net'

const SECRET = 'my-webhook-secret-abc123'
function secretOk(got) {
  if (typeof got !== 'string') return false
  const a = Buffer.from(got), b = Buffer.from(SECRET)
  return a.length === b.length && timingSafeEqual(a, b)
}
const tg = new BlockList()
tg.addSubnet('149.154.160.0', 20, 'ipv4')
tg.addSubnet('91.108.4.0', 22, 'ipv4')

for (const [name, hdr, ip] of [
  ['정상',               SECRET,                    '149.154.167.41'],
  ['시크릿 없음',         undefined,                 '149.154.167.41'],
  ['시크릿 틀림',         'wrong-secret',            '149.154.167.41'],
  ['길이만 같고 틀림',     'my-webhook-secret-XXXXX', '149.154.167.41'],
  ['시크릿 맞지만 외부IP',  SECRET,                    '203.0.113.9'],
  ['두 번째 대역',        SECRET,                    '91.108.5.200'],
]) {
  const s = secretOk(hdr), i = tg.check(ip, 'ipv4')
  console.log(`${s && i ? '통과' : '거부'}  ${name.padEnd(20)} secret=${String(s).padEnd(5)} ip=${i}`)
}
```

```bash
node webhook.mjs
```

실제 출력입니다.

```
통과  정상                   secret=true  ip=true
거부  시크릿 없음               secret=false ip=true
거부  시크릿 틀림               secret=false ip=true
거부  길이만 같고 틀림            secret=false ip=true
거부  시크릿 맞지만 외부IP         secret=true  ip=false
통과  두 번째 대역              secret=true  ip=true
```

**시크릿을 알아도 대역 밖이면 막히고, 대역 안이어도 시크릿이 없으면 막힙니다.**

> 단, 이건 **IP 검사를 켰을 때** 이야기입니다. 위 가드는 `CHECK_IP` 가 기본 꺼짐이라 **시크릿만으로 판단**합니다. 아래를 읽고 켤지 정하세요.

## 🚨 가장 중요한 부분 — 빼기만 하면 구멍입니다

2편 끝에서 전역 가드를 권했습니다. 웹훅은 JWT가 없으니 그대로 두면 죽습니다. 그래서 이렇게들 씁니다.

```ts
// ❌ 절대 이렇게 하지 마세요
if (req.path.startsWith('/webhook')) return true   // 인증 건너뛰기
```

**`/webhook` 으로 시작하는 모든 경로가 인증 없이 열렸습니다.** 텔레그램만 통과하는 게 아니라 **아무나** 통과합니다.

**제외와 대체는 다릅니다.**

```
JWT 가드를 비켜가게 한다  →  그 자리에 웹훅 가드를 채운다
        (빼기)                        (채우기)
```

2편의 `@Public()` 을 쓰면 이렇게 됩니다.

```ts
@Controller('webhook/telegram')
@Public()                          // ← 전역 JWT 가드는 비켜간다
@UseGuards(TelegramWebhookGuard)   // ← 대신 시크릿 가드가 지킨다
export class TelegramController { /* ... */ }
```

> **여기서 NestJS 의 중요한 성질 하나.** 컨트롤러에 `@UseGuards` 를 붙여도 **전역 가드가 없어지지 않습니다.** 둘 다 돕니다. 그래서 `@Public()` 없이 `@UseGuards(TelegramWebhookGuard)` 만 붙이면, **전역 JWT 가드가 먼저 401 을 던져서 웹훅이 죽습니다.** 두 줄이 세트입니다.

**`@Public()` 만 붙이고 `@UseGuards` 를 빠뜨리면** 그 경로는 완전히 열립니다. `startsWith('/webhook')` 과 똑같은 구멍이죠. **한 줄 빠졌을 뿐인데 결과는 같습니다.**

## 잘 되고 있는지 확인하는 법

여기까지 오면 걱정이 하나 생깁니다. **막고 있는 게 공격자인지 텔레그램인지 어떻게 알까요?**

텔레그램이 알려줍니다.

```bash
curl "https://api.telegram.org/bot<봇토큰>/getWebhookInfo"
```

세 필드를 보세요.

| 필드 | 뜻 |
|---|---|
| `pending_update_count` | 쌓여서 못 보낸 업데이트 수 |
| `last_error_date` | 마지막 실패 시각 |
| `last_error_message` | 실패 이유 |

**여기에 에러가 쌓여 있으면 제 쪽이 막고 있는 것입니다.** IP 검사를 켰다가 대역이 안 맞거나, `::ffff:` 문제에 걸렸거나요.

> 앞에서 "대역이 바뀌면 봇이 조용히 죽는다"고 했는데, 정확히는 **완전히 조용하진 않습니다.** 텔레그램은 2XX 가 아니면 **재시도하다가 포기**하고, 그 기록을 여기 남깁니다. **다만 여러분이 보러 가지 않으면 모릅니다.** 배포 후 한 번은 찍어보세요.

## 경로를 추측하기 어렵게

경로에 무작위 문자열을 섞으면(`/webhook/telegram/8f3a...`) 스캐너에 덜 걸립니다. **다만 이건 보안이 아니라 소음 감소입니다** — 0편에서 말한 그대로, 주소를 모른다는 게 방어는 아닙니다.

## 체크리스트

- [ ] `setWebhook` 에 **`secret_token` 을 넣어 등록**했다
- [ ] 헤더 `X-Telegram-Bot-Api-Secret-Token` 을 **`timingSafeEqual` 로** 비교한다
- [ ] IP 검사를 **켰다면**, `req.ip` 를 실측해서 텔레그램 대역이 찍히는 걸 확인했다 (안 찍히면 **끈다**)
- [ ] `getWebhookInfo` 로 **에러가 쌓이고 있지 않은지** 확인했다
- [ ] **JWT 가드에서 뺀 경로에 웹훅 가드가 붙어 있다**
- [ ] 시크릿이 **환경변수/시크릿 매니저**에 있고 커밋되지 않았다
- [ ] **봇 토큰**도 같은 수준으로 보관돼 있다 — 이게 새면 공격자가 `setWebhook` 으로 **업데이트 흐름을 통째로 자기 서버로 돌릴 수 있습니다**
- [ ] 시크릿이 샜을 때 **`setWebhook` 으로 교체**하면 된다는 걸 알고 있다

## 확인 못 한 것

- **위 실험은 검증 로직만 떼어내 돌린 것**입니다. 실제 텔레그램에서 오는 요청으로는 확인하지 못했습니다.
- **텔레그램 IP 대역이 언제 바뀌는지.** 공식 문서에 갱신 정책이 없습니다. 그래서 이 글은 IP 를 **보조 수단**으로만 씁니다.
- **Cloud Run 앞단 구성에 따라 `req.ip` 가 무엇이 되는지.** 4편에서 다루지만, 조합마다 달라 일반화하지 않았습니다. 켜기 전에 **직접 찍어보라**고 한 이유입니다.
- 위 실행 결과는 **Node `net.BlockList`, Express 5.2.1** 기준입니다.

---

## 정리

- 웹훅은 **로그인을 요구할 수 없는 유일한 문**입니다. 신원 대신 **공유 비밀**로 지킵니다.
- **`secret_token`이 1차 방어**, IP 대역은 보조입니다. 공식 문서가 **대역이 바뀔 수 있다**고 명시합니다.
- 비교는 **`timingSafeEqual`**, 길이를 먼저 확인.
- **`req.ip`가 프록시 IP가 아닌지** 확인하세요.
- **제외 ≠ 안전.** `@Public()` 과 `@UseGuards` 는 **세트**입니다. 하나만 붙이면 죽거나 열립니다.
- **IP 검사는 선택**입니다. 켜기 전에 `req.ip` 를 실측하고, `::ffff:` 를 벗기세요.
- **봇 토큰이 시크릿보다 강력합니다.** 새면 웹훅 자체를 남의 서버로 돌릴 수 있습니다.

다음 편은 **뒷문**입니다. 0편에서 본 `*.run.app` 우회를 실제로 막습니다 — 무료로 기본 URL을 끄는 법, Cloudflare 앞단, Cloud Armor 셋을 비교합니다.

> 이전 편: [2편. 진짜 인증 경계 — Supabase JWT 검증하기](./02-verify-jwt.md)
> 다음 편: [4편. 뒷문 — Cloud Run 직접 호출 막기](./04-backdoor.md)
