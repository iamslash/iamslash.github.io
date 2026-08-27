# 6편. 나가는 문 — Cloud Run에서 PlanetScale로

> 시리즈: 내 스택 안전하게 만들기
> 이 편에서 배우는 것: 나가는 연결도 문이라는 것, `sslmode=require` 가 왜 부족한지 **직접 확인해보기**, Node 의 `pg` 는 `psql` 과 다르게 동작한다는 함정, 그리고 비밀번호를 어디에 둘 것인가.

지금까지 다섯 편 동안 **들어오는 문**만 봤습니다. 브라우저, 웹훅, `run.app` 뒷문, WebSocket, MCP.

그런데 문은 하나 더 있습니다. **나가는 문**입니다.

```
    [ 들어오는 문 ]                        [ 나가는 문 ]
브라우저 ─┐                        ┌─→ PlanetScale (DB 비밀번호)
웹훅     ─┼─→ Cloud Run (NestJS) ─┤
MCP      ─┘                        └─→ Telegram API (봇 토큰)
```

들어오는 문은 **모르는 사람이 두드립니다.** 나가는 문은 **내가 직접 엽니다.** 그래서 안전하게 느껴지는데, 사실은 반대입니다.

**나가는 연결에는 자격증명이 실려 있습니다.** DB 비밀번호, 봇 토큰. 들어오는 요청을 막는 데 실패하면 공격자가 *문을 두드릴* 수 있지만, 나가는 연결이 엉뚱한 곳에 닿으면 **공격자가 열쇠를 통째로 받습니다.**

---

## 나가는 연결은 상대를 확인하지 않습니다

이런 줄이 어딘가에 있을 겁니다.

```
DATABASE_URL=postgres://user:pass@xxxx.horizon.psdb.cloud:5432/mydb?sslmode=require
```

`sslmode=require` — 암호화를 **요구**한다니 안전해 보이죠. 그런데 이게 정확히 무엇을 보장할까요?

표를 읽기 전에 한 가지만. TLS 연결에서 서버는 **인증서**를 내밉니다 — *"나는 `xxxx.psdb.cloud` 다. 이 사실을 OO 인증기관(**CA**, Certificate Authority)이 보증한다"* 는 증명서입니다. 이 증명서를 **얼마나 깐깐하게 검사할지** 정하는 게 `sslmode` 입니다.

PostgreSQL 공식 문서의 표를 그대로 옮기면 이렇습니다. [문서]

| sslmode | 도청 방어 | **중간자(MITM) 방어** |
|---|---|---|
| `require` | Yes | **No** |
| `verify-ca` | Yes | CA 정책에 따라 다름 |
| `verify-full` | Yes | **Yes** |

`require` 는 자물쇠는 채우는데 **누구 집 문인지 확인을 안 하는** 겁니다. 표의 **중간자 방어 `No`** 가 바로 이 뜻입니다.

### 직접 확인해봅시다

말로만 하면 안 믿기니 직접 해봅시다. **공격자 서버를 하나 세웁니다.** 인증서 이름을 아예 `attacker-in-the-middle` 로 박아둡니다.

실제 공격에서는 DNS 조작이나 네트워크 경유지 탈취로, **여러분이 PlanetScale 주소로 연결했다고 믿는 사이에** 이런 서버로 연결됩니다. 그래서 **중간자**(MITM)입니다. 실험에서는 그 '엉뚱한 서버'에 곧장 붙어서, **클라이언트가 눈치채는지만** 봅니다.

```bash
docker network create pglab-net
docker volume create pglab-certs

# 자체 서명 인증서 — 이름은 대놓고 '공격자'
docker run --rm -v pglab-certs:/certs postgres:16 bash -c '
  openssl req -new -x509 -days 1 -nodes -out /certs/server.crt -keyout /certs/server.key \
    -subj "/CN=attacker-in-the-middle" 2>/dev/null
  chown 999:999 /certs/server.*  &&  chmod 600 /certs/server.key'   # 999 = 컨테이너의 postgres 유저

docker run -d --name pglab-db --network pglab-net -e POSTGRES_PASSWORD=secret \
  -v pglab-certs:/certs:ro postgres:16 \
  -c ssl=on -c ssl_cert_file=/certs/server.crt -c ssl_key_file=/certs/server.key
```

이제 `pglab-db` 로 접속합니다. 서버가 내미는 인증서에는 `attacker-in-the-middle` 이라 적혀 있죠. **이름이 완전히 다릅니다.**

```bash
run() { docker run --rm --network pglab-net -v pglab-certs:/certs:ro -e PGPASSWORD=secret \
  postgres:16 psql "host=pglab-db user=postgres dbname=postgres $1" -tAc "select 1"; }

run "sslmode=require"                                        # ①
run "sslmode=verify-full sslrootcert=system"                 # ②
run "sslmode=verify-ca   sslrootcert=/certs/server.crt"      # ③
run "sslmode=verify-full sslrootcert=/certs/server.crt"      # ④
```

실제 결과입니다. [관찰]

```
① sslmode=require                                  ← 암호화만 요구
1                                                  ← 붙었습니다. 공격자 서버에.

② sslmode=verify-full sslrootcert=system           ← 시스템 CA로 검증
psql: error: ... SSL error: certificate verify failed

③ sslmode=verify-ca sslrootcert=/certs/server.crt  ← 공격자 인증서를 CA로 신뢰
1                                                  ← 붙었습니다. CA는 맞으니까.

④ sslmode=verify-full sslrootcert=/certs/server.crt ← 같은 CA + 이름 검증
psql: error: ... server certificate for "attacker-in-the-middle"
              does not match host name "pglab-db"
```

`1` 은 `select 1` 이 성공했다는 뜻입니다. ① — **비밀번호가 암호화된 채로, 공격자에게 그대로 넘어갔습니다.** ③ — `verify-ca` 는 "믿는 기관이 발급했나"만 보고 **"내가 부른 그 서버가 맞나"는 안 봅니다.** 이름까지 보는 건 `verify-full` 뿐입니다.

실험이 끝나면 지우세요.

```bash
docker rm -f pglab-db && docker network rm pglab-net && docker volume rm pglab-certs
```

> **PlanetScale 이 요구하는 값도 이겁니다.** 공식 문서에 *"Set to `verify-full` for secure connections (required)"* 라고 못 박혀 있습니다. [문서] 예시 연결 문자열에 붙은 `sslrootcert=system` 은 **OS 가 이미 신뢰하는 CA 목록**을 쓰겠다는 뜻이고요.
>
> **🚨 단 `sslrootcert=system` 은 `psql` 전용입니다.** Node 의 `pg` 는 `sslrootcert` 를 **파일 경로**로 읽어서, `system` 이라는 파일을 찾다가 `ENOENT: no such file or directory, open 'system'` 으로 **`new Pool()` 하는 순간 터집니다.** [관찰] Node 에서는 필요도 없습니다 — `pg` 는 내장 CA 목록으로 검증하고 PlanetScale 인증서는 공개 CA 가 발급했으니까요. **`DATABASE_URL` 에는 `?sslmode=verify-full` 만 넣으세요.**

---

## 🚨 함정 — Node 의 `pg` 는 `psql` 과 다릅니다

여기서 멈추면 안 됩니다. NestJS 는 `psql` 이 아니라 **Node 의 `pg` 라이브러리**로 붙습니다. 같을까요?

같은 공격자 서버에 `pg` 8.23.0 으로 붙여봤습니다. [관찰]

```
① connectionString 에 ?sslmode=verify-full   → 거부됨 ✅ 막힘
② connectionString 에 ?sslmode=require       → 거부됨 ✅ 막힘   ← psql 과 다름!
③ ssl: { rejectUnauthorized: false }         → 연결됨 ⚠️ 뚫림   ← 암호화는 됨(TLSv1.3)
④ ssl: true                                  → 거부됨 ✅ 막힘
⑤ ssl 옵션 아예 없음                          → 연결됨 ⚠️ 뚫림   ← 평문! 암호화조차 안 됨
```

(코드는 생략합니다 — 같은 도커 네트워크에서 `pg` 의 `Client` 에 위 ①~⑤ 옵션만 바꿔 넣으면 재현됩니다.)

**세 가지가 튀어나옵니다.**

**첫째, ②가 `psql` 과 반대입니다.** `pg` 는 `require` 를 `verify-full` 처럼 취급합니다. 더 안전한 쪽으로요. 그런데 실행하면 이런 경고가 같이 뜹니다. [관찰]

> *"SECURITY WARNING: ... In the next major version (pg-connection-string v3.0.0 and pg v9.0.0), these modes will adopt standard libpq semantics, which have **weaker security guarantees**."*

**지금 `require` 로 안전한 건 우연이고, 다음 메이저 버전에서 사라집니다.** 그때 조용히 약해집니다 — 에러도 안 나고, 로그도 안 남고, 그냥 검증을 그만둡니다. 라이브러리가 알아서 챙겨주는 데 기대지 말고 **`verify-full` 이라고 직접 쓰세요.**

**둘째, ③이 진짜 구멍입니다.** `ssl: { rejectUnauthorized: false }` — "인증서 에러 나면 이거 넣으세요"로 돌아다니는 인터넷 튜토리얼의 단골입니다. 이름 그대로 **"인가되지 않은 것을 거부하지 않겠다"**는 뜻입니다. 공격자 서버에 그대로 붙습니다.

**셋째, ⑤는 평문입니다.** `ssl` 옵션을 아예 안 주면 암호화조차 안 합니다. (PlanetScale 은 *"All PlanetScale Postgres connections require SSL/TLS encryption"* 이라 서버가 거절하지만 [문서], **로컬 개발 DB 는 그냥 통과합니다.** 로컬에서 되던 게 배포하면 안 되는 이유가 대개 이겁니다.)

### 그래서 이렇게 쓰세요

```ts
// ✅ 연결 문자열에 명시 — 라이브러리 기본값에 기대지 않는다
// DATABASE_URL=postgres://user:pass@host:5432/db?sslmode=verify-full
```

연결 문자열에 `sslmode` 가 있으면 **`ssl` 옵션을 통째로 덮어씁니다.** 그래서 `?sslmode=verify-full` 을 쓰면 코드 어딘가에 `rejectUnauthorized: false` 가 남아 있어도 **막힙니다.** [관찰]

**로컬 개발 때문에 `rejectUnauthorized: false` 를 넣고 싶다면**, 그게 운영에 절대 안 닿도록 **부팅할 때 막으세요.**

```ts
// 운영에서만 검사한다 — 호스트 이름을 문자열로 추측하지 않는다
if (process.env.NODE_ENV === 'production') {
  const url = process.env.DATABASE_URL ?? ''
  if (!url.includes('sslmode=verify-full')) {
    throw new Error('운영 DB 연결에 sslmode=verify-full 이 없습니다')  // 부팅 시 즉시 실패
  }
}
```

**조용히 약해지는 것보다 시끄럽게 죽는 게 낫습니다.**

---

## 비밀번호를 어디에 둘 것인가

`verify-full` 로 상대는 확인했습니다. 이제 **열쇠 자체**를 봅시다.

`gcloud run deploy --set-env-vars DATABASE_URL=postgres://...` 로 넣으면, 비밀번호가 **배포 명령어에 그대로** 들어갑니다. 셸 히스토리, CI 로그, 서비스 설정 화면 — 콘솔에서 서비스를 볼 수 있는 사람은 전부 볼 수 있습니다.

Google Secret Manager 를 쓰세요. Cloud Run 에 붙이는 방법이 **두 가지**인데, 차이가 중요합니다. [문서]

| | 환경변수로 | 볼륨으로(파일) |
|---|---|---|
| 값을 읽는 시점 | **인스턴스 시작 때 한 번** | **읽을 때마다** |
| 비밀번호를 바꾸면 | 재배포해야 반영 | 다음 읽기부터 반영 |

```bash
# 환경변수로 — 간단, 대신 버전을 고정
gcloud run deploy api --set-secrets=DATABASE_URL=db-url:3

# 볼륨으로 — 회전에 유리
gcloud run deploy api --set-secrets=/secrets/db-url=db-url:latest
```

**둘 중 하나를 고르세요.** `--set-secrets` 는 더하기가 아니라 **교체**라서, 연달아 실행하면 앞엣것이 사라집니다.

문서의 권고입니다 — *"Google recommends that you **pin the secret to a particular version instead of using `latest`**"*. [문서]

**환경변수인데 `latest` 를 쓰면 인스턴스마다 다른 비밀번호를 들고 있을 수 있습니다.** 새로 뜬 인스턴스는 새 값, 이미 떠 있던 인스턴스는 옛 값. 비밀번호를 바꾼 직후 **"어떤 요청은 되고 어떤 요청은 안 되는"** 유령 같은 장애가 여기서 나옵니다.

서비스 계정(Cloud Run 이 실행될 때 쓰는 GCP 계정)에 `roles/secretmanager.secretAccessor` 를 주는 것도 잊지 마세요. [문서]

---

## 여기까지가 무료입니다

지금까지 한 건 **돈이 안 듭니다.** 연결 문자열에 `sslmode=verify-full`(글자 몇 개), Secret Manager, 부팅 시 검증(코드 세 줄).

**그리고 이게 방어의 대부분입니다.** 다음 단계부터는 돈이 듭니다.

---

## 한 걸음 더 — IP 로 잠그기 (돈이 듭니다)

`verify-full` 은 **내가 엉뚱한 서버에 붙는 걸** 막습니다. 반대 방향은 못 막습니다 — **비밀번호가 유출되면**, 공격자는 자기 노트북에서 그냥 붙습니다.

PlanetScale Postgres 에 IP 제한이 있습니다. [문서]

> *"You can now define which IP addresses can connect to **each branch** for PlanetScale Postgres databases using IP restrictions."*

규칙은 **브랜치마다** 걸고, **역할(role)** 이나 **스키마**로 더 좁힐 수 있습니다. 운영 브랜치는 Cloud Run 에서만, 개발 브랜치는 사무실에서만 — 이렇게 나누는 게 기본 사용법입니다.

**그런데 문제가 있습니다. Cloud Run 은 나가는 IP 가 고정이 아닙니다.** 허용할 IP 자체가 없죠.

고정하려면 나가는 트래픽(**egress**)을 전부 **VPC**(내 전용 가상 네트워크)로 모은 뒤, **Cloud NAT**(여러 인스턴스가 하나의 IP 로 나가게 해주는 관문)에 고정 IP 를 붙여 내보내야 합니다. [문서]

```bash
gcloud run deploy api \
  --network=NETWORK --subnet=SUBNET \
  --vpc-egress=all-traffic       # ← 모든 트래픽을 VPC 로
```

### 비용을 정직하게 말하면

VPC 와 서브넷은 무료지만 **Cloud NAT 와 고정 IP 는 아닙니다.** 게이트웨이 **VM 시간당**(인스턴스가 많아지면 시간당 정액으로 상한), 처리 데이터 **GiB 당**, 고정 IP **시간당** — 세 갈래로 붙습니다. [문서]

파산할 금액은 아닙니다. **문제는 금액보다, 지금까지와 달리 0원이 아니고 관리할 부품이 넷(VPC·서브넷·NAT·방화벽) 늘어난다는 점입니다.** (0편에서 말했듯 정확한 금액은 적지 않습니다 — 공식 계산기로 확인하세요.)

### 그래서 할 만한가?

**대부분의 1인/소규모 서비스라면 지금은 아닙니다.** 순서가 있습니다.

| 먼저 (0원) | 나중에 (유료) |
|---|---|
| `sslmode=verify-full` | 고정 egress IP + IP 제한 |
| Secret Manager + 버전 고정 | |
| 환경별 비밀번호 분리 | |

**비밀번호 분리는 공짜인데 효과가 큽니다.** PlanetScale 은 DB 를 git 브랜치처럼 복제해서 씁니다(예: 운영은 `main`, 개발은 `dev`). 비밀번호는 **브랜치 하나에만** 유효하므로, 개발용 비밀번호가 새도 운영 DB 는 안전합니다. 운영 비밀번호를 로컬 `.env` 에 두는 습관만 버려도 IP 제한이 막아줄 위험의 상당 부분이 사라집니다.

IP 제한이 값을 하는 시점은 **다룰 데이터가 무거워졌을 때**, 그리고 **비밀번호를 만지는 사람이 여럿이 됐을 때**입니다.

---

## DB 말고 다른 나가는 문

같은 원칙이 나머지에도 적용됩니다.

- **Telegram API 호출** — 봇 토큰이 실려 나갑니다. URL 을 **하드코딩**하세요. 토큰은 Secret Manager 에.
- **사용자가 준 URL 로 요청 보내기** — 이건 다른 종류의 위험입니다. 사용자가 넣은 주소로 서버가 대신 요청을 보내주면, 공격자는 **여러분 서버를 발판 삼아** 바깥에서 못 닿는 곳에 닿습니다. **SSRF**(Server-Side Request Forgery)라고 부릅니다. 있다면 **허용 목록** 방식으로 막고, 없다면 만들지 마세요.

> `--vpc-egress=all-traffic` 을 켜면 **모든** 나가는 트래픽이 VPC 를 지납니다. 두 가지를 같이 챙겨야 합니다.
>
> - **인터넷**(Telegram API, PlanetScale) — Cloud NAT 가 없으면 그대로 끊깁니다.
> - **Google API**(Secret Manager 등) — 서브넷에 **Private Google Access** 를 켜야 합니다. 안 켜면 **방금 Secret Manager 에 넣은 비밀번호를 못 읽습니다.**
>
> **들어오는 트래픽에는 영향이 없습니다.** WebSocket 연결도 Telegram 웹훅 수신도 그대로입니다 — 이건 **나가는 방향 전용** 설정입니다.

---

## 체크리스트

- [ ] 연결 문자열에 **`sslmode=verify-full` 이 명시**되어 있다 (기본값에 기대지 않는다)
- [ ] 코드 어디에도 **`rejectUnauthorized: false`** 가 없다
- [ ] 운영 부팅 시 **연결 설정을 검증하고 실패하면 죽는다**
- [ ] DB 비밀번호가 **`--set-env-vars` 평문이 아니라 `--set-secrets`**(Secret Manager 참조)로 들어간다
- [ ] 환경변수로 넣었다면 **버전을 고정**했다 (`latest` 아님)
- [ ] **개발용과 운영용 비밀번호가 다르다**
- [ ] 운영 비밀번호가 **로컬 `.env` 에 없다**
- [ ] 봇 토큰 등 나가는 자격증명도 **Secret Manager** 에 있다

---

## 확인 못 한 것

- **IP 제한 규칙이 하나도 없을 때의 기본 동작.** 문서에 명시가 없습니다. 아무 IP나 되는 것으로 보이지만 확인 못 했습니다.
- **IP 제한이 어느 요금제부터인지, 추가 비용이 있는지.** 문서에서 못 찾았습니다.
- **Cloud NAT 요금의 정확한 월 합계.** Cloud Run 에서 "VM 개수"를 어떻게 세는지 확인 못 했습니다. 위 금액은 어림입니다.
- 위 실험은 **로컬 도커 Postgres 16 / `pg` 8.23.0** 기준입니다. `pg` 는 v9.0.0 에서 동작이 바뀐다고 예고되어 있습니다.

---

## 정리

- **나가는 연결도 문입니다.** 들어오는 문과 달리 **자격증명이 실려 나갑니다.**
- **`require` 는 중간자를 못 막고, `verify-ca` 는 CA 정책에 기댑니다.** 내가 부른 **이름까지** 확인하는 건 **`verify-full`** 뿐 — 문서 표와 실험 양쪽으로 확인했습니다.
- **Node `pg` 는 다음 메이저 버전에서 약해집니다.** `verify-full` 을 **명시**하고, `rejectUnauthorized: false` 는 절대 쓰지 마세요.
- **비밀번호는 Secret Manager 에.** 환경변수로 넣었다면 **버전을 고정**하세요.
- **고정 IP + IP 제한은 유료입니다.** 먼저 공짜인 것부터 — 그게 방어의 대부분입니다.

이번 편은 **서버의 열쇠**(DB 비밀번호)였습니다. 마지막 편은 **사용자의 열쇠** — 1편부터 미뤄온 질문입니다. 브라우저가 JWT 를 들고 있어야 할까요, BFF 가 들고 있어야 할까요?

> 이전 편: [5편. 긴 연결 문 — WebSocket과 MCP](./05-long-connections.md)
> 다음 편: [7편. 토큰을 어디에 둘 것인가 — BFF와 쿠키](./07-token-storage.md)
