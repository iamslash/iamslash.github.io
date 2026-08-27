# 2편. 진짜 인증 경계 — Supabase JWT 검증하기

> 시리즈: 내 스택 안전하게 만들기
> 이 편에서 배우는 것: 반드시 확인해야 할 네 가지, NestJS 가드 코드, 공격 5종을 실제로 막아보기, 그리고 가장 흔한 실수 하나.

이 구성에는 **RLS(Row Level Security — DB가 행 단위로 접근을 거르는 기능) 같은 마지막 방어선이 없습니다.** 데이터는 PlanetScale에 있고, 거기 닿는 유일한 길이 NestJS입니다. (Supabase 를 인증 전용으로만 쓰는 경우입니다.)

```
브라우저 ─(JWT)→ BFF ─(JWT)→ NestJS ─→ PlanetScale
                              ↑
                       여기가 뚫리면 뒤가 없다
```

그래서 이 편이 시리즈에서 가장 중요합니다.

## 확인해야 할 네 가지

JWT를 받으면 **네 가지**를 봐야 합니다. 하나라도 빠지면 구멍입니다.

| 확인 | 안 하면 |
|---|---|
| **서명** | 누구나 토큰을 위조 |
| **`exp`** (만료) | 옛 토큰이 영원히 유효 |
| **`iss`** (발급자) | **같은 키로 서명된** 다른 용도의 토큰이 통과 (심층 방어) |
| **`aud`** (대상) | 다른 용도의 토큰이 통과 |

1편에서 **디코드 ≠ 검증**이라고 했죠. 디코드는 봉투를 뜯는 것이고, 검증은 **도장이 진짜인지 확인**하는 것입니다.

## NestJS 가드

> **먼저 확인하세요.** 아래 코드는 프로젝트가 **비대칭키(JWT signing keys)로 서명할 때** 동작합니다. 예전 방식인 **공유 시크릿(HS256)** 을 쓰고 있다면 시크릿은 공개될 수 없으니 JWKS 에 없고, **모든 요청이 401 로 떨어집니다.** Supabase 대시보드에서 어느 쪽인지 먼저 보세요. (1편에서 디코드해본 토큰의 `alg` 가 `HS256` 이면 아직 대칭키입니다.)

`jose` 라이브러리를 씁니다. Supabase의 공개키(**JWKS** — JSON Web Key Set, 공개키 목록)를 받아 캐시해줍니다.

```bash
npm i jose
```

```ts
// auth.guard.ts
import { CanActivate, ExecutionContext, Injectable,
         UnauthorizedException, ServiceUnavailableException } from '@nestjs/common'
import { createRemoteJWKSet, jwtVerify } from 'jose'

const ISS = `${process.env.SUPABASE_URL}/auth/v1`

// ★ 모듈 레벨에 한 번만. 내부적으로 공개키를 캐시한다
const JWKS = createRemoteJWKSet(new URL(`${ISS}/.well-known/jwks.json`))

@Injectable()
export class SupabaseAuthGuard implements CanActivate {
  async canActivate(ctx: ExecutionContext): Promise<boolean> {
    const req = ctx.switchToHttp().getRequest()

    // Bearer 는 대소문자를 가리지 않는다 (RFC 7235)
    const [scheme, token] = (req.headers.authorization ?? '').split(' ')
    if (scheme?.toLowerCase() !== 'bearer' || !token) {
      throw new UnauthorizedException('no token')
    }

    try {
      const { payload } = await jwtVerify(token, JWKS, {
        issuer: ISS,                       // ← iss 확인
        audience: 'authenticated',         // ← aud 확인
        requiredClaims: ['sub', 'exp'],    // ← 클레임이 '있는지'까지 확인
      })                                   // ← 서명은 jwtVerify 가 자동으로

      // ★ 사용자 ID 는 오직 여기서만 꺼낸다
      req.user = { id: payload.sub as string }
      return true
    } catch (e: any) {
      // 공개키를 못 가져온 건 토큰 문제가 아니다 — 장애로 드러나게
      if (e?.code === 'ERR_JWKS_TIMEOUT' || e?.code === 'ERR_JWKS_NO_MATCHING_KEY') {
        throw new ServiceUnavailableException('auth key unavailable')
      }
      throw new UnauthorizedException('invalid token')
    }
  }
}
```

핵심은 세 줄입니다.

- **`createRemoteJWKSet`을 모듈 레벨에** 두세요. 요청마다 만들면 매번 공개키를 새로 받아옵니다.
- **`issuer`와 `audience`를 반드시 넘기세요.** 안 넘기면 확인을 건너뜁니다.
- **`payload.sub`가 사용자 ID입니다.** 다른 데서 가져오면 안 됩니다.

> **`requiredClaims`를 왜 넣었을까요?** `jwtVerify`는 `exp`가 **있으면** 확인하지만, **아예 없는 토큰은 그냥 통과**시킵니다. `exp` 를 뺀 토큰으로 직접 확인했습니다. [관찰]
>
> ```
> requiredClaims 없음 → 통과 ⚠️
> requiredClaims 있음 → 거부 ✅ ERR_JWT_CLAIM_VALIDATION_FAILED
> ``` `sub`도 마찬가지고, 그러면 `payload.sub`가 `undefined`인 채로 흘러갑니다. 실제 Supabase 토큰에는 늘 있지만, **없으면 거부**가 맞습니다.

> 서명은 `jwtVerify`가 알아서 봅니다. 하지만 `iss`/`aud`/`requiredClaims`는 **여러분이 명시해야** 합니다. 이게 빠진 코드를 자주 봅니다.

## 정말 막히는지 확인해봅시다

말로만 하면 안 되니 **공격 토큰을 직접 만들어** 던져보겠습니다. 검증 로직은 위와 같고, 키만 로컬에서 만듭니다.

```js
// attack.mjs
import { generateKeyPair, SignJWT, jwtVerify, exportJWK,
         createLocalJWKSet, base64url } from 'jose'

const ISS = 'https://abcdefgh.supabase.co/auth/v1'
const AUD = 'authenticated'

const { publicKey, privateKey } = await generateKeyPair('ES256')
const jwks = createLocalJWKSet({ keys: [{ ...(await exportJWK(publicKey)), alg: 'ES256' }] })

const mint = (opts = {}) =>
  new SignJWT({ role: 'authenticated' })
    .setProtectedHeader({ alg: 'ES256' })
    .setIssuer(opts.iss ?? ISS).setAudience(opts.aud ?? AUD)
    .setSubject('user-111').setIssuedAt()
    .setExpirationTime(opts.exp ?? '1h')
    .sign(privateKey)

const verify = (t) => jwtVerify(t, jwks, { issuer: ISS, audience: AUD })

const good     = await mint()
const expired  = await mint({ exp: Math.floor(Date.now()/1000) - 60 })
const wrongIss = await mint({ iss: 'https://evil.example.com/auth/v1' })
const wrongAud = await mint({ aud: 'some-other-app' })

// 공격 ①: 페이로드를 admin 으로 고치고 서명은 그대로 붙이기
const [h, p, sig] = good.split('.')
const t = JSON.parse(new TextDecoder().decode(base64url.decode(p)))
t.role = 'admin'
const forged = h + '.' +
  base64url.encode(new TextEncoder().encode(JSON.stringify(t))) + '.' + sig

// 공격 ②: alg 를 none 으로 바꾸고 서명 지우기
const noneHdr = base64url.encode(
  new TextEncoder().encode(JSON.stringify({ alg: 'none', typ: 'JWT' })))
const algNone = noneHdr + '.' + p + '.'

for (const [name, tok] of [
  ['정상 토큰', good], ['페이로드 위조 (role→admin)', forged],
  ['alg: none 공격', algNone], ['만료된 토큰', expired],
  ['다른 발급자(iss)', wrongIss], ['다른 대상(aud)', wrongAud],
]) {
  try {
    const { payload } = await verify(tok)
    console.log('통과  ' + name.padEnd(24) + ' sub=' + payload.sub + ' role=' + payload.role)
  } catch (e) {
    console.log('거부  ' + name.padEnd(24) + ' ' + (e.code ?? e.name))
  }
}
```

```bash
npm i jose && node attack.mjs
```

실제 출력입니다. (`jose` 6.2.10) [관찰]

```
통과  정상 토큰                    sub=user-111 role=authenticated
거부  페이로드 위조 (role→admin)     ERR_JWS_SIGNATURE_VERIFICATION_FAILED
거부  alg: none 공격             ERR_JOSE_NOT_SUPPORTED
거부  만료된 토큰                   ERR_JWT_EXPIRED
거부  다른 발급자(iss)              ERR_JWT_CLAIM_VALIDATION_FAILED
거부  다른 대상(aud)               ERR_JWT_CLAIM_VALIDATION_FAILED
```

**다섯 가지 공격이 전부 막혔습니다.** 하나씩 보면:

- **페이로드 위조** — 1편에서 말한 그대로입니다. `role`을 `admin`으로 고칠 수는 있지만 **새 서명을 만들 수 없습니다.**
- **`alg: none`** — "서명 알고리즘이 없다"고 우기는 고전적 공격입니다. 라이브러리가 아예 지원하지 않습니다.
- **만료된 토큰** — `exp`는 옵션을 안 넘겨도 잡힙니다.
- **다른 발급자·다른 대상** — `iss`/`aud`를 넘겼기 때문에 걸립니다. **안 넘겼다면 통과했을 것**입니다.

> **`iss`/`aud`를 빼고 한 번 돌려보세요.** 발급자와 대상이 다른 토큰이 그냥 통과합니다. 그게 이 두 줄의 값어치입니다.

## 가장 흔한 실수 — 바디의 `user_id`

지금까지는 라이브러리가 막아줬습니다. **이건 라이브러리가 못 막습니다.**

```ts
// ❌ 이렇게 하면 안 됩니다
@Post('posts')
async create(@Body() dto: CreatePostDto) {
  return this.posts.create({ userId: dto.userId, ... })
  //                                 ↑ 클라이언트가 보낸 값
}
```

토큰 검증은 통과했습니다. 그런데 **`userId`를 요청 바디에서 꺼냈습니다.** 공격자는 자기 토큰으로 로그인한 뒤 남의 ID를 적어 보내면 됩니다.

```json
{ "userId": "남의-uuid", "title": "..." }
```

**검증된 JWT의 `sub`에서만** 꺼내세요.

```ts
// ✅ 이렇게
@Post('posts')
@UseGuards(SupabaseAuthGuard)
async create(@Req() req, @Body() dto: CreatePostDto) {
  return this.posts.create({ userId: req.user.id, ... })
  //                                 ↑ 가드가 넣어준 값
}
```

### 역할은 어디서 가져와야 하나

여기서 함정이 하나 더 있습니다. Supabase JWT 에는 `role` 클레임이 있는데, **이건 앱 역할이 아닙니다.**

```json
"role": "authenticated"   ← 로그인한 모든 사용자가 이 값입니다
```

공식 문서가 이 클레임을 *"The Postgres role to use when applying Row Level Security policies"* 라고 설명합니다. [문서] **관리자든 일반 사용자든 똑같습니다.** 이걸로 관리자 라우트를 막으면 아무도 못 막습니다.

그럼 어디서 가져올까요? **두 곳은 안 됩니다.**

| 출처 | 왜 안 되나 |
|---|---|
| 요청 바디·헤더 | 클라이언트가 마음대로 씁니다 |
| **`user_metadata`** | **클라이언트가 직접 수정 가능합니다** — 스스로 admin 이 될 수 있습니다 |

`user_metadata` 가 특히 위험합니다. 이름 때문에 안전해 보이지만, 공식 문서가 이렇게 못 박습니다. [문서]

> *"Do not use it in security sensitive context (such as in RLS policies or authorization logic), as this value is **editable by the user without any checks**."*

로그인한 사용자가 클라이언트에서 한 줄이면 됩니다.

```js
await supabase.auth.updateUser({ data: { role: 'admin' } })
```

안전한 곳은 둘입니다.

- **여러분 DB(PlanetScale)에서 `sub` 로 조회** ← RBAC 를 NestJS 에 두셨으니 이쪽이 자연스럽습니다
- **`app_metadata`** — 서버에서만 쓸 수 있는 영역

```ts
// 가드에서는 신원만 확정하고
req.user = { id: payload.sub as string }

// 역할은 내 DB 에서 sub 로 조회
const role = await this.users.findRoleByAuthId(req.user.id)
```

1편의 그림 2 에서 **"sub 로 사용자 특정 → RBAC 역할 판정"** 이라고 그렸던 게 이 순서입니다.

> **원칙 하나로 정리하면**: *클라이언트가 보낸 값 중 신원에 관한 것은 하나도 믿지 않는다.* 신원은 **오직 검증된 토큰에서만** 나옵니다.

## 토큰이 만료되면

Supabase 액세스 토큰은 기본이 한 시간(3600 초)입니다. [문서] 만료되면 어떻게 될까요?

**`exp` 를 늘리는 건 답이 아닙니다.** 토큰은 훔쳐가면 그대로 쓸 수 있으니(1편), 수명이 길수록 피해가 커집니다.

정답은 **리프레시 토큰**입니다. 별도의 긴 수명 토큰으로 새 액세스 토큰을 받아옵니다. BFF 가 있다면 **이 갱신을 서버에서 처리**할 수 있습니다 — 7편의 주제입니다.

여기서는 하나만 기억하세요. **"한 시간 뒤 로그아웃된다"는 증상을 만나면 `exp` 를 늘리지 말고 갱신을 붙이세요.**

## 대칭키를 쓰고 있다면

1편에서 본 대로입니다 — 대칭키를 쓰면 NestJS가 **위조 능력까지** 갖게 됩니다. Supabase 공식 문서도 공유 시크릿(HS256)에 대해 *"Not recommended for production applications."* 라고 명시합니다. [문서]

어느 쪽인지는 1편에서 배운 디코드로 바로 압니다. 헤더의 `alg`가 `HS256`이면 대칭키, `ES256`/`RS256`이면 비대칭키입니다.

> 전환은 Supabase 대시보드에서 하는 작업인데, **화면 구성이 버전에 따라 달라집니다.** 이 글에 절차를 박아두면 금방 낡으니, 대시보드의 JWT 설정 항목을 찾아 공식 문서대로 진행하세요.

## 체크리스트

배포 전에 이것만 확인하세요.

- [ ] `jwtVerify`에 **`issuer`와 `audience`를 넘기고 있다**
- [ ] `createRemoteJWKSet`이 **요청마다 새로 만들어지지 않는다**
- [ ] 사용자 ID를 **`req.user.id`(=`payload.sub`)에서만** 꺼낸다
- [ ] 역할은 **토큰의 `role` 이 아니라 내 DB 에서** 온다
- [ ] 토큰이 없거나 깨졌을 때 **401을 던진다** (조용히 통과 금지)
- [ ] **웹훅 경로는 이 가드에서 제외**돼 있다 — 단 **제외한 경로는 3편의 시크릿 검증이 대신 지켜야 합니다.** 검증 없이 열어두면 그냥 구멍입니다

마지막 항목이 중요합니다. 텔레그램은 JWT를 못 보냅니다.

### 전역으로 걸 것인가

지금까지는 라우트마다 `@UseGuards` 를 붙였습니다. 빠뜨리면 **그 라우트만 조용히 열립니다.**

반대로 전역에 걸면 기본이 "막힘"이 되고, 열 곳만 표시하면 됩니다.

```ts
// app.module.ts
providers: [{ provide: APP_GUARD, useClass: SupabaseAuthGuard }]
```

```ts
// 열어야 하는 곳만 표시
export const Public = () => SetMetadata('isPublic', true)
```

그리고 가드가 그 표시를 보고 비켜줍니다.

```ts
constructor(private reflector: Reflector) {}

async canActivate(ctx: ExecutionContext) {
  const isPublic = this.reflector.getAllAndOverride<boolean>('isPublic',
    [ctx.getHandler(), ctx.getClass()])
  if (isPublic) return true
  // ... 아래는 앞의 검증 코드와 동일
}
```

> **어느 쪽이 나을까요?** 라우트별은 **빠뜨리면 열리고**, 전역은 **빠뜨리면 401 로 시끄럽게 죽습니다.** 보안에서는 후자가 낫습니다 — 조용한 구멍보다 요란한 고장이 낫거든요.
>
> 다만 **`@Public()` 을 붙이는 것만으로는 부족합니다.** 그 자리에 다른 검증을 채워야 하고, 그게 다음 편입니다.

## 확인 못 한 것

- **위 공격 실험은 로컬에서 만든 키**로 돌렸습니다. 실제 Supabase 프로젝트의 JWKS 로는 확인하지 못했습니다. 검증 로직은 같지만, 발급 측 설정(키 종류·클레임 구성)은 프로젝트마다 다를 수 있습니다.
- **`app_metadata` 를 클라이언트가 못 고친다**는 것. 문서에서 `user_metadata` 쪽 경고만 확인했고, `app_metadata` 의 쓰기 권한을 명시한 문장은 못 찾았습니다. 확실한 건 **내 DB 에서 조회하는 쪽**입니다.
- **대시보드에서 비대칭키로 전환하는 절차.** 화면 구성이 자주 바뀌어 이 글에 적지 않았습니다.
- 위 실행 결과는 **`jose` 6.2.10** 기준입니다.

---

## 정리

- 확인할 건 **네 가지** — 서명, `exp`, `iss`, `aud`.
- **서명과 `exp`는 자동, `iss`/`aud`는 직접 넘겨야** 합니다.
- 위조·`alg:none`·만료·발급자·대상 **다섯 공격이 전부 막히는 걸 실행으로 확인**했습니다.
- **라이브러리가 못 막는 건 하나** — 바디의 `user_id`를 믿는 것. 신원은 **`sub`에서만**.
- **역할은 토큰의 `role` 이 아니라 내 DB 에서** 가져오세요. `user_metadata` 는 클라이언트가 고칩니다.
- 가능하면 **비대칭키**를 쓰세요.

다음 편은 **잠글 수 없는 문**입니다. 텔레그램 웹훅을 어떻게 검증하고, 왜 이 가드에서 빼야 하는지.

> 이전 편: [1편. JWT가 뭔가](./01-what-is-jwt.md)
> 다음 편: [3편. 웹훅 문 — 잠글 수 없는 문 지키기](./03-webhook.md)
