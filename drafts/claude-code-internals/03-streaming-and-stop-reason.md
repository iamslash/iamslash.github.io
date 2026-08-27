# 3편. 응답 — SSE 스트리밍과 stop_reason

> 시리즈: Claude Code 내부 구조 (builtin 기준, v2.1.243)
> 이 편에서 배우는 것: 응답이 조각조각 도착하는 순서, 툴 호출 인자가 어떻게 스트리밍되는지, 그리고 **`stop_reason` 하나가 루프 전체를 좌우한다**는 것.

2편에서 요청을 다 조립해서 보냈습니다. 이제 돌아오는 쪽을 봅니다.

## 왜 스트리밍인가

2편에서 본 요청 바디에 이 줄이 있었습니다.

```
stream = true
```

Claude Code 는 **항상** 스트리밍으로 요청합니다. 이유는 두 가지입니다.

**첫째, 화면에 글자가 하나씩 찍히게 하려고.** 이건 눈에 보이는 이유입니다.

**둘째, 이게 더 중요한데 — 응답이 다 오기 전에 일을 시작하려고.** 모델이 "Bash 툴을 이렇게 부르겠다"는 블록을 완성하는 순간, 뒤에 무슨 말이 더 나올지 기다리지 않고 바로 실행에 들어갈 수 있습니다. 4편에서 자세히 봅니다.

## 실제 SSE 를 눈으로 보기

Claude Code 에는 원시 스트림을 그대로 뱉는 옵션이 있습니다.

```bash
claude -p "run echo hi" --permission-mode bypassPermissions \
  --output-format stream-json --include-partial-messages --verbose \
| python3 -c "
import sys,json
for l in sys.stdin:
    try: o=json.loads(l)
    except: continue
    if o.get('type')=='stream_event':
        print('SSE ->', o['event']['type'], json.dumps(o['event'])[:150])
    else:
        print(o.get('type'), o.get('subtype',''))"
```

> `--permission-mode bypassPermissions` 는 권한 프롬프트 없이 툴을 실행합니다. **실험용 디렉터리에서만** 쓰세요. 5편에서 권한 모드를 다룹니다.

실제 출력입니다(툴 호출 1회 왕복). [관찰]

```
system init
system status(requesting)
SSE -> message_start        {"message":{"id":"msg_...","usage":{...}}}
SSE -> content_block_start  {"index":0,"content_block":{"type":"text","text":""}}
SSE -> content_block_delta  {"index":0,"delta":{"type":"text_delta","text":"Let me check."}}
SSE -> content_block_stop   {"index":0}
SSE -> content_block_start  {"index":1,"content_block":{"type":"tool_use","id":"toolu_...","name":"Bash","input":{}}}
SSE -> content_block_delta  {"index":1,"delta":{"type":"input_json_delta","partial_json":"{\"command\":\"echo hi\"}"}}
SSE -> content_block_stop   {"index":1}
SSE -> message_delta        {"delta":{"stop_reason":"tool_use","stop_sequence":null},"usage":{"output_tokens":5}}
SSE -> message_stop
user                        ← tool_result 생성
system status(requesting)   ← 루프 2회전
SSE -> message_start ... message_delta {"stop_reason":"end_turn"} ... message_stop
result
```

## 이벤트 순서 해부

위 출력을 구조로 정리하면 이렇습니다.

```
message_start                  ← 응답 하나 시작. id, model, usage 초안
  content_block_start  index=0 ← 블록 0 시작 (type: text)
  content_block_delta  index=0 ← 글자 조각들이 계속 온다
  content_block_delta  index=0
  content_block_stop   index=0 ← 블록 0 끝
  content_block_start  index=1 ← 블록 1 시작 (type: tool_use)
  content_block_delta  index=1 ← 인자 JSON 조각들
  content_block_stop   index=1
message_delta                  ← ★ stop_reason 이 여기 온다
message_stop                   ← 응답 하나 끝
```

핵심은 **`content_block` 이 여러 개**라는 점입니다. 모델의 한 응답은 텍스트 하나가 아닙니다.

```
[0] text     "Let me check."      ← 사람에게 하는 말
[1] tool_use Bash {"command":...} ← 기계에게 하는 말
```

한 응답 안에 사람용 문장과 툴 호출이 **같이** 들어 있습니다. 그래서 Claude Code 가 "확인해볼게요"라고 말하면서 동시에 명령을 실행하는 것처럼 보이는 겁니다. 실제로 같은 응답입니다.

전체 이벤트 타입은 여덟 가지입니다. [문서] 이 중 앞의 여섯은 직접 관찰했습니다. [관찰]

```
message_start · content_block_start · content_block_delta · content_block_stop
message_delta · message_stop · ping · error
```

## `input_json_delta` — 툴 인자도 조각으로 온다

`delta` 에도 종류가 있습니다. [문서]+[관찰]

| delta 타입 | 무엇 |
|---|---|
| `text_delta` | 일반 텍스트 조각 |
| `input_json_delta` | **툴 호출 인자 JSON 조각** |
| `thinking_delta` | 확장 사고 조각 |
| `signature_delta` | 사고 블록 서명 |

`input_json_delta` 가 흥미롭습니다. 툴 인자가 **완성된 JSON 으로 한 번에 오지 않습니다.** 문자열 조각으로 옵니다.

```
{"partial_json": "{\"comm"}
{"partial_json": "and\":\"echo "}
{"partial_json": "hi\"}"}
```

받는 쪽에서 이어붙여야 유효한 JSON 이 됩니다. 그래서 조각을 다 받기 전에는 **파싱할 수 없습니다.** `content_block_stop` 이 와야 비로소 "이 툴을 이 인자로 부르면 되겠다"가 확정됩니다.

> 큰 파일을 쓰는 `Write` 툴 호출이 유독 느리게 느껴진 적 있나요? 파일 내용 전체가 이 `partial_json` 조각으로 흘러오기 때문입니다. 모델이 파일을 한 글자씩 "타이핑"하고 있는 셈입니다.

바이너리에서도 이 문자열들을 확인할 수 있습니다. [관찰]

```bash
B=$(ls -d ~/.local/share/claude/versions/* | tail -1)
for s in message_start content_block_delta input_json_delta thinking_delta message_delta message_stop; do
  printf "%-22s %s\n" "$s" "$(LC_ALL=C grep -ac -- "$s" "$B")"
done
```

## `stop_reason` — 루프를 좌우하는 단 하나의 값

이제 이 편의 핵심입니다. `message_delta` 이벤트에 실려 오는 `stop_reason` 이 **다음에 무슨 일이 일어날지를 혼자서 결정합니다.**

0편의 의사코드를 다시 봅시다.

```python
response = call_llm(...)
messages.append(response)

if response.stop_reason != "tool_use":
    break                          # ← 여기
results = [run_tool(b) for b in response.tool_use_blocks]
messages.append({"role": "user", "content": results})
```

`stop_reason` 값별 의미와 루프 동작입니다.

| 값 | 의미 | 루프 동작 |
|---|---|---|
| `tool_use` | 툴을 부르고 싶다 | 툴 실행 → `tool_result` 를 user 메시지로 붙임 → **재요청** [관찰] |
| `end_turn` | 할 말 다 했다 | **루프 종료.** 사람 입력 대기 [관찰] |
| `max_tokens` | `max_tokens` 한도에 걸림 | 응답이 잘림 [문서] |
| `stop_sequence` | 정지 시퀀스에 걸림 | 아래 참고 [관찰] |
| `pause_turn` | 서버 툴 반복 한도 | 그대로 재전송해 재개 [문서] |
| `refusal` | 모델이 거부 | 폴백 처리 [관찰] |
| `model_context_window_exceeded` | 컨텍스트 초과 | [문서] |

### 실측 분포 — 루프는 생각보다 많이 돈다

제 머신의 전체 세션에서 `stop_reason` 을 세어봤습니다.

```bash
cd ~/.claude/projects && python3 -c "
import json,glob,collections
s=collections.Counter(); m=collections.Counter()
for f in glob.glob('*/*.jsonl'):
    for l in open(f):
        try: o=json.loads(l)
        except: continue
        if o.get('type')=='assistant':
            s[repr(o['message'].get('stop_reason'))]+=1; m[o['message'].get('model')]+=1
print('stop_reason:',s.most_common())
print('model      :',m.most_common(6))"
```

```
stop_reason: [("'tool_use'", 92457), ("'end_turn'", 13540), ("'stop_sequence'", 114), ('None', 13)]
model      : [('claude-opus-5', 51556), ('claude-opus-4-8', 39884), ('claude-fable-5', 14567), ('<synthetic>', 114), ...]
```

이 두 숫자를 나눠보세요. [관찰]

```
tool_use 92,457 ÷ end_turn 13,540 ≈ 6.8
```

**`end_turn` 한 번당 `tool_use` 가 평균 6.8 번입니다.** 제가 질문 하나를 던지면 Claude Code 는 평균 **일곱 번쯤 API 를 왕복하고 나서야** 대답을 돌려준다는 뜻입니다.

> 여기서 0편의 "매번 전부 다시 보낸다"가 왜 중요한지 실감이 옵니다. 질문 하나에 요청이 일곱 번 나가고, **그때마다 대화 전체가 다시 전송됩니다.** 2편에서 본 프롬프트 캐싱이 없다면 비용이 감당이 안 됩니다.

### `stop_sequence` 114 건의 정체

표에서 `stop_sequence` 가 114 건 보입니다. 그런데 모델 이름을 같이 세어보니 `<synthetic>` 이 정확히 **114 건**입니다. 숫자가 일치합니다.

`<synthetic>` 은 실제 모델 응답이 아니라 **Claude Code 가 스스로 만들어 대화에 끼워 넣은 가짜 assistant 메시지**입니다. [관찰] 인터럽트 같은 상황에서 대화 구조를 맞추려고 씁니다. 4편에서 실물을 봅니다.

> 데이터를 분석할 때 이런 걸 조심해야 합니다. **`<synthetic>` 을 걸러내지 않으면 "모델이 stop_sequence 로 멈춘다"는 잘못된 결론**에 도달합니다. 실제로는 모델이 만든 게 아닙니다.

## 실패하면 어떻게 되나

네트워크는 끊깁니다. API 는 가끔 과부하가 납니다. 이때 트랜스크립트에 `api_error` 레코드가 남습니다.

```bash
cd ~/.claude/projects && python3 -c "
import json,glob,collections
n=0; c=collections.Counter()
for f in glob.glob('*/*.jsonl'):
    for l in open(f):
        if 'api_error' not in l: continue
        try: o=json.loads(l)
        except: continue
        if o.get('subtype')=='api_error':
            n+=1; c[(o.get('error') or {}).get('formatted','?')[:60]]+=1
print('api_error 총',n,'건')
for k,v in c.most_common(5): print(' ',v,k)"
```

제 머신 결과입니다. [관찰]

```
api_error 총 252 건
  198 Unable to connect to API (ECONNRESET)
   19 Unable to connect to API (ConnectionRefused)
   18 529 Overloaded
   10 Unable to connect to API (FailedToOpenSocket)
    7 Request timed out.
```

레코드 하나를 열어보면 재시도 정책이 그대로 보입니다. [관찰]

```json
{"type":"system", "subtype":"api_error", "level":"error",
 "error":{"message":"Connection error.",
          "formatted":"Unable to connect to API (ECONNRESET)",
          "connection":{"code":"ECONNRESET","isSSLError":false}},
 "retryInMs":509.44, "retryAttempt":1, "maxRetries":10}
```

**최대 10 회, 지수 백오프**입니다. `retryInMs` 가 509ms 에서 시작해 재시도마다 늘어납니다.

> 252 건이나 실패했는데 제 작업은 대부분 멀쩡히 끝났습니다. **재시도가 조용히 처리해준 것**입니다. "Claude Code 가 잠깐 멈췄다가 다시 움직이는" 순간이 대개 이겁니다.

## 정리

- Claude Code 는 **항상 스트리밍**으로 요청합니다. 화면 표시 때문만이 아니라, 응답이 끝나기 전에 툴 실행을 시작하기 위해서입니다.
- 한 응답은 **content block 여러 개**입니다. 사람에게 하는 말(`text`)과 기계에게 하는 말(`tool_use`)이 한 응답에 같이 들어 있습니다.
- 툴 인자는 **`input_json_delta` 조각**으로 옵니다. 다 이어붙여야 파싱됩니다.
- **`stop_reason` 이 루프를 좌우합니다.** `tool_use` 면 계속, 아니면 종료.
- 실측하면 **`end_turn` 하나당 `tool_use` 가 평균 6.8 번**입니다. 질문 하나에 API 왕복이 일곱 번쯤 일어납니다.
- `<synthetic>` 모델 응답은 Claude Code 가 만든 가짜입니다. 통계 낼 때 걸러야 합니다.
- API 실패는 **최대 10 회 지수 백오프**로 조용히 재시도됩니다.

## 확인 못 한 것

1. **`max_tokens` 와 `model_context_window_exceeded` 는 실제로 보지 못했습니다.** 제 트랜스크립트의 약 10만 6천 건 assistant 레코드 중 단 한 건도 없었습니다. 의미는 공식 문서 기준입니다. [문서]
2. `pause_turn` 도 미관찰입니다. 서버 사이드 툴을 쓰는 경우에 나타나는 값입니다.
3. `stop_details` 라는 필드가 응답 봉투에 존재하지만, 관찰한 모든 샘플에서 비어 있었습니다.

다음 편에서는 드디어 **루프 자체**를 봅니다. `stop_reason` 이 `tool_use` 로 왔을 때 정확히 무슨 일이 일어나는지 — 툴이 언제 실행되는지(놀랍게도 스트리밍이 끝나기 **전**입니다), 여러 개면 동시에 도는지, ESC 를 누르면 어떻게 되는지.

> 이전 편: [2편. 요청 바디 해부 — LLM에게 실제로 보내는 것](./02-request-body.md)
> 다음 편: [4편. Agent loop — while 루프 하나가 전부다](./04-agent-loop.md)
