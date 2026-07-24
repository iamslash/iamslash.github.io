# 발행 트래커 — 대용량 메시지 처리: Erlang 에서 Elixir 까지

이 디렉터리(`drafts/erlang-to-elixir/`)의 글은 전부 **draft** 다. mdBook 은 `book.toml` 의 `src = "src"`
설정에 따라 `src/` 만 빌드하므로, 여기 있는 한 사이트에 절대 뜨지 않는다(소스는 공개 repo 엔 보임).
한 편을 검수·확정하면 아래 순서대로 하나씩 발행한다.

## 발행 방법 (한 편씩)

1. 파일을 src 로 이동:
   `mv drafts/erlang-to-elixir/<파일> src/ko/erlang-to-elixir/`
   (첫 발행이면 먼저 `mkdir -p src/ko/erlang-to-elixir`)
2. `src/SUMMARY.md` 의 `# 한국어` 섹션 아래에 해당 줄을 추가.
   첫 발행 시 섹션 헤더 `# 대용량 메시지 처리: Erlang 에서 Elixir 까지` 도 함께 추가.
3. 커밋 + push → GitHub Actions 가 빌드·배포.

로컬 미리보기: 보고 싶은 draft 를 임시로 src 로 옮겨 `mdbook serve` 로 확인 후 되돌리거나,
발행 직전에 옮겨서 확인한다. (`mdbook` 미설치 시 `cargo install mdbook`)

**주의:** 순서대로 내는 중이라면, 먼저 발행된 글의 "다음 글" 링크가 아직 미발행인 다음 글을
가리켜 그 순간엔 404 가 될 수 있다(다음 편을 발행하면 해소). 신경 쓰이면 발행 시 그 링크를 붙이자.

## 읽기 순서와 발행 목록 (체크하며 진행)

- [ ] **01** — `mv drafts/erlang-to-elixir/01-why-erlang-succeeded.md src/ko/erlang-to-elixir/`
  - SUMMARY: `- [왜 그들은 Erlang 으로 성공했는가](./ko/erlang-to-elixir/01-why-erlang-succeeded.md)`
- [ ] **02** — `mv drafts/erlang-to-elixir/02-concurrency.md src/ko/erlang-to-elixir/`
  - SUMMARY: `- [동시성: 수백만 프로세스와 BEAM 스케줄러](./ko/erlang-to-elixir/02-concurrency.md)`
- [ ] **02b** — `mv drafts/erlang-to-elixir/02b-concurrency-vs-parallelism.md src/ko/erlang-to-elixir/`
  - SUMMARY: `- [동시성과 병렬성: 100만은 논리적 동시성이다](./ko/erlang-to-elixir/02b-concurrency-vs-parallelism.md)`
- [ ] **03** — `mv drafts/erlang-to-elixir/03-isolation-supervision.md src/ko/erlang-to-elixir/`
  - SUMMARY: `- [격리성과 감독성: Let It Crash 와 OTP 감독 트리](./ko/erlang-to-elixir/03-isolation-supervision.md)`
- [ ] **04** — `mv drafts/erlang-to-elixir/04-modern-tools.md src/ko/erlang-to-elixir/`
  - SUMMARY: `- [BEAM 밖에서 같은 특성 좇기](./ko/erlang-to-elixir/04-modern-tools.md)`
- [ ] **05** — `mv drafts/erlang-to-elixir/05-why-elixir.md src/ko/erlang-to-elixir/`
  - SUMMARY: `- [왜 Elixir 인가, 그리고 언제 아닌가](./ko/erlang-to-elixir/05-why-elixir.md)`
- [ ] **06** — `mv drafts/erlang-to-elixir/06-system-design.md src/ko/erlang-to-elixir/`
  - SUMMARY: `- [시스템 디자인: 멀티채널 LLM 챗봇](./ko/erlang-to-elixir/06-system-design.md)`
- [ ] **07** — `mv drafts/erlang-to-elixir/07-channel-gateway.md src/ko/erlang-to-elixir/`
  - SUMMARY: `- [채널 게이트웨이: 어댑터 패턴](./ko/erlang-to-elixir/07-channel-gateway.md)`
- [ ] **08** — `mv drafts/erlang-to-elixir/08-conversation-core.md src/ko/erlang-to-elixir/`
  - SUMMARY: `- [대화 코어: GenServer 상태와 LLM 스트리밍](./ko/erlang-to-elixir/08-conversation-core.md)`
- [ ] **09** — `mv drafts/erlang-to-elixir/09-throttling-durability.md src/ko/erlang-to-elixir/`
  - SUMMARY: `- [부하 조절과 내구성, 그리고 POC 너머](./ko/erlang-to-elixir/09-throttling-durability.md)`

### 심화 · 부록 (본편 09 이후, 선택 발행 · junior 눈높이)

- [ ] **10** — `mv drafts/erlang-to-elixir/10-why-no-k8s.md src/ko/erlang-to-elixir/`
  - SUMMARY: `- [왜 보통은 K8s·Redis·Kafka 가 필요했을까](./ko/erlang-to-elixir/10-why-no-k8s.md)`
- [ ] **11** — `mv drafts/erlang-to-elixir/11-scale-out-without-k8s.md src/ko/erlang-to-elixir/`
  - SUMMARY: `- [K8s 없이 scale out 하기: libcluster·분산 메시징·Horde](./ko/erlang-to-elixir/11-scale-out-without-k8s.md)`

앞으로 새로 쓰는 글도 기본적으로 이 `drafts/` 아래에 두고, 검수 후 같은 방식으로 발행한다.
