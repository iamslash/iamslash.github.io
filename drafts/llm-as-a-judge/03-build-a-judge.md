# 3편. LLM judge 만들기

> 시리즈: AI 답변을 채점하는 법 — LLM-as-a-Judge 밑바닥부터
> 이 편에서 배우는 것: 2편의 채점 메모를 rubric으로 바꾸는 법, judge의 출력 스키마를 설계할 때 **필드 순서가 정확도를 바꾸는** 이유, few-shot 예제를 넣는 방법과 그때 조심해야 할 정보 누출, 그리고 실행 가능한 코드 전체.

이제 judge를 만듭니다. 결론부터 말하면 **judge는 프롬프트 한 장과 JSON 스키마 하나**입니다. 생각보다 간단하고, 그래서 대충 만들기 쉽습니다. 정확도를 가르는 건 몇 가지 요령입니다.

## rubric 쓰기 — 2편의 메모가 초안입니다

2편에서 채점하며 적어둔 메모를 다시 꺼냅니다.

```
[채점 기준 메모]
- 로그인 고객에게 주문번호 되묻기 → FAIL
- 배송일을 "곧"이라고만 하면 → FAIL, 날짜 필요
- 사과만 하고 해결책 없으면 → FAIL
- 이모지 1~2개는 OK, 3개 이상은 감점
```

이걸 rubric으로 옮깁니다. 그전에, 흔한 실패작부터 봅시다.

### 나쁜 rubric

```
아래 고객 상담 답변이 좋은 답변인지 평가하라.
PASS 또는 FAIL로 답하라.
```

동작은 합니다. 그런데 **"좋은"의 정의가 없어서 judge가 자기 취향대로 판단합니다.** 0편에서 봤던 사고가 정확히 여기서 납니다 — judge는 "정중하게 정보를 요청했으니 좋은 응대"라고 생각하는데, 우리 팀은 "되묻는 게 문제"라고 생각하죠.

### 좋은 rubric

```
당신은 온라인 원두 쇼핑몰 "콩마켓"의 고객 상담 품질 검수자다.
상담원의 답변 한 개를 평가한다.

## 평가 질문
"이 답변을 그대로 고객에게 보내도 되는가?"

## FAIL 조건 (하나라도 해당하면 FAIL)
1. 고객이 로그인 상태(logged_in=true)인데 주문번호·이메일 등
   이미 조회 가능한 정보를 되물었다.
2. 배송/환불 시점을 "곧", "빠른 시일 내" 같은 모호한 표현으로만
   말하고 구체적 날짜를 주지 않았다.
3. 사과나 공감만 하고, 상담원이 할 수 있는 조치를 안 했다.
   (예: "죄송합니다, 고객센터로 문의해 주세요")
4. 사실과 다른 정보를 말했다. (제공된 주문/상품 정보와 불일치)

## PASS 조건
위 FAIL 조건에 해당하지 않고, 고객이 물은 것에 실제로 답했다.

## 평가하지 말 것
- 말투나 이모지 사용량은 평가 대상이 아니다.
- 답변 길이는 평가 대상이 아니다. 짧아도 필요한 정보가 있으면 PASS.
- 당신이라면 다르게 썼을 것 같다는 이유로 FAIL을 주지 마라.

## 판정
- 명확히 FAIL 조건에 해당 → FAIL
- 명확히 문제없음 → PASS
- 정보가 부족해 판단할 수 없음 → UNCLEAR
```

차이가 뭘까요.

**첫째, FAIL 조건을 번호로 나열했습니다.** "좋은 답변"이라는 추상어 대신 구체적 행동을 적었습니다. judge는 추상어를 자기 마음대로 해석하지만, 번호 붙은 조건은 그대로 따릅니다.

**둘째, "평가하지 말 것"이 있습니다.** 이게 의외로 큰 효과를 냅니다. judge에게 그냥 평가를 시키면 **온갖 것에 트집을 잡습니다.** 말투가 딱딱하다, 이모지가 없다, 좀 짧다… 우리가 궁금한 건 그게 아닌데 말이죠. 범위를 명시적으로 잘라주면 judge가 본론에 집중합니다.

**셋째, UNCLEAR의 조건을 정했습니다.** "애매하면 UNCLEAR"가 아니라 "**정보가 부족해서** 판단 불가일 때"라고 좁혔습니다. 이렇게 안 하면 judge가 어려운 케이스를 전부 UNCLEAR로 도망칩니다.

> **rubric 작성 요령 한 줄:** 사람 신입 검수자에게 주는 업무 지시서라고 생각하고 쓰세요. **"알아서 잘 판단해주세요"** 라고 쓰지 않을 겁니다.

## 출력 스키마 — 필드 순서가 정확도를 바꿉니다

judge에게 자유롭게 답하게 하면 파싱이 지옥이 됩니다. 요즘은 대부분의 API가 **구조화 출력(structured output)** 을 지원하니 그걸 씁니다.

```python
from pydantic import BaseModel, Field
from typing import Literal

class Finding(BaseModel):
    quote: str = Field(description="답변에서 그대로 인용한 문장")
    issue: str = Field(description="이 문장이 어떤 조건에 해당하는지")

class Judgment(BaseModel):
    findings: list[Finding]                          # ① 근거
    reasoning: str                                    # ② 종합
    verdict: Literal["PASS", "FAIL", "UNCLEAR"]      # ③ 판정
```

> **처음 보는 두 가지**
> - **Pydantic** — 파이썬에서 데이터 형태를 클래스로 선언하고 검증해주는 라이브러리입니다(`pip install pydantic`). 여기서는 이 클래스가 그대로 **LLM에게 줄 JSON 스키마**로 변환됩니다.
> - **`Literal["PASS", "FAIL", "UNCLEAR"]`** — "이 셋 중 하나만"이라는 뜻입니다. LLM이 `"괜찮음"` 같은 엉뚱한 값을 내지 못하게 막습니다.

**여기서 필드 순서가 결정적입니다.**

LLM은 텍스트를 **왼쪽에서 오른쪽으로** 생성합니다. 구조화 출력도 마찬가지로 JSON을 앞에서부터 씁니다. 그러니 스키마를 이렇게 짜면:

```python
# ❌ 나쁜 순서
class Judgment(BaseModel):
    verdict: Literal["PASS", "FAIL"]   # 먼저 생성됨
    reasoning: str                      # 나중
```

judge는 **판정을 먼저 뱉고, 그다음에 그 판정에 맞는 이유를 지어냅니다.** 사람으로 치면 결론을 내지르고 나서 논리를 갖다 붙이는 것과 같습니다.

반대로 근거를 먼저 쓰게 하면, judge는 답변을 실제로 뜯어본 뒤에 판정합니다. 인용문까지 강제하면 더 좋습니다 — 없는 내용을 지어내기 어려워지니까요.

> **한 줄 규칙: `verdict`는 스키마의 맨 마지막 필드여야 합니다.**

이 규칙의 근거는 두 층입니다.

**확실한 것:** LLM은 앞에서 뒤로 생성하므로, 앞에 놓인 필드가 뒤에 놓인 필드의 조건이 됩니다. `verdict`를 먼저 두면 그 뒤의 `reasoning`은 **이미 정해진 결론을 설명하는 글**이 되고, 뒤에 두면 앞서 쓴 근거를 **읽고 나서** 내리는 판정이 됩니다. 이건 생성 방식에서 바로 따라오는 사실입니다.

**방향이 같은 연구:** G-Eval(Liu et al., 2023)은 평가 절차를 chain-of-thought로 먼저 쓰게 한 뒤 점수를 매기는 방식이 사람 판단과 더 잘 맞는다는 걸 보였습니다. 다만 **이 논문이 "JSON 필드 순서"를 실험한 것은 아닙니다** — "근거를 먼저, 판정을 나중에"라는 같은 방향의 결과일 뿐, 필드 순서 규칙의 직접적인 증명은 아니라는 점을 구분해 두세요.

**그래서 어떻게 해야 하나:** 순서를 바꿔보고 **직접 재세요.** 4편의 검증을 두 스키마로 각각 돌리면 어느 쪽이 나은지 몇 분 만에 나옵니다. 사람 라벨이 이미 있으니 공짜에 가까운 실험입니다.

`findings`의 부수 효과도 큽니다. 4편에서 judge와 사람이 불일치한 케이스를 분석할 때, **judge가 어느 문장을 보고 그렇게 판단했는지** 알 수 있어서 원인 파악이 훨씬 빨라집니다.

## 전체 코드

이제 붙여봅시다. OpenAI SDK 형태로 썼지만, Anthropic·Gemini·오픈소스 모델 어느 쪽이든 구조는 같습니다.

> **버전 주의:** 아래는 `openai` 파이썬 SDK **1.x** 기준입니다. 구조화 출력 진입점이 SDK 버전에 따라 `client.beta.chat.completions.parse(...)` 였다가 정식 승격되면서 `client.chat.completions.parse(...)` 로 옮겨갔습니다. **설치된 버전의 공식 문서를 먼저 확인**하고, `AttributeError`가 나면 `beta.`를 붙이거나 떼면 됩니다. 나머지 로직은 동일합니다.

```python
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Literal

client = OpenAI()

RUBRIC = """당신은 온라인 원두 쇼핑몰 "콩마켓"의 고객 상담 품질 검수자다.
...(위의 rubric 전문)...
"""

class Finding(BaseModel):
    quote: str
    issue: str

class Judgment(BaseModel):
    findings: list[Finding]
    reasoning: str
    verdict: Literal["PASS", "FAIL", "UNCLEAR"]


def render(case: dict) -> str:
    """테스트 케이스의 '상황'(고객 정보 + 대화 맥락)을 문자열로 만든다.
    5편의 pairwise judge도 이 함수를 그대로 쓴다."""
    conversation = "\n".join(
        f"{'고객' if m['role'] == 'user' else '콩돌이'}: {m['content']}"
        for m in case["context"]
    )
    return (
        f"## 고객 정보\n"
        f"로그인 상태: {case['metadata']['logged_in']}\n\n"
        f"## 대화 맥락\n{conversation}"
    )


def judge(case: dict, response: str) -> Judgment | None:
    """케이스 하나와 챗봇 답변 하나를 채점한다.
    None 이면 판정 실패(모델 거부 또는 파싱 실패) — 호출 측에서 UNCLEAR 로 다룬다."""

    completion = client.chat.completions.parse(
        model="gpt-4.1-mini",           # judge 모델 (아래에서 설명)
        temperature=0,                   # 재현성을 위해 0
        messages=[
            {"role": "system", "content": RUBRIC},
            {"role": "user", "content":
                f"{render(case)}\n\n## 평가 대상 답변\n콩돌이: {response}"},
        ],
        response_format=Judgment,
    )

    message = completion.choices[0].message
    if message.refusal is not None or message.parsed is None:
        return None
    return message.parsed
```

`judge()`가 `None`을 돌려줄 수 있다는 점이 중요합니다. 모델이 안전 이유로 답변을 거부하거나 스키마에 맞지 않는 출력을 내면 파싱이 실패하는데, **이걸 무시하면 4편에서 "judge가 몇 개를 판정 못 했나"를 셀 수 없게 됩니다.** 실패는 실패로 남겨두세요.

실행해보면 이런 게 나옵니다.

```python
>>> case = {
...     "context": [{"role": "user", "content": "어제 주문한 거 아직도 안 왔어요"}],
...     "metadata": {"logged_in": True},
... }
>>> result = judge(case, "주문번호를 알려주시면 확인해 드릴게요!")
>>> print(result.model_dump_json(indent=2, ensure_ascii=False))
{
  "findings": [
    {
      "quote": "주문번호를 알려주시면 확인해 드릴게요!",
      "issue": "FAIL 조건 1 — 로그인 고객에게 조회 가능한 정보를 되물음"
    }
  ],
  "reasoning": "고객이 로그인 상태이므로 최근 주문을 직접 조회해 안내할 수 있었다. 되묻는 것은 고객에게 부담을 전가한 것.",
  "verdict": "FAIL"
}
```

0편에서 PASS를 줬던 그 judge가, rubric을 제대로 쓰니 FAIL을 줍니다.

## 데이터셋 전체 돌리기

케이스 200개를 순차로 돌리면 오래 걸립니다. 병렬로 던지되 동시 실행 수를 제한하세요.

```python
import asyncio

async def _judge_all_async(cases: dict, responses: dict, concurrency: int):
    # Semaphore = 동시에 통과할 수 있는 개수를 제한하는 신호등.
    # 8개까지만 동시에 API를 호출하고, 나머지는 자리가 날 때까지 기다린다.
    sem = asyncio.Semaphore(concurrency)

    async def one(case_id: str):
        async with sem:
            result = await asyncio.to_thread(
                judge, cases[case_id], responses[case_id]
            )
            return case_id, result

    pairs = await asyncio.gather(*[one(cid) for cid in cases])
    return {
        cid: (result.verdict if result is not None else "UNCLEAR")
        for cid, result in pairs
    }


def judge_all(cases: dict, responses: dict, concurrency: int = 8) -> dict:
    """{case_id: "PASS" | "FAIL" | "UNCLEAR"} 를 돌려준다.
    cases 와 responses 는 둘 다 case_id 를 키로 하는 dict."""
    return asyncio.run(_judge_all_async(cases, responses, concurrency))
```

**반환값이 `{case_id: 판정}` 형태의 dict**라는 점을 기억해 두세요. 4편의 검증과 6편의 비교가 전부 이 모양을 전제로 합니다. 판정에 실패한 케이스(`judge()`가 `None`)는 `UNCLEAR`로 들어갑니다.

**동시 실행 수는 8~16 정도가 무난합니다.** 더 올리면 rate limit에 걸립니다. 200건이면 보통 1~3분이면 끝납니다.

## judge 모델은 무엇으로 할까

세 가지 원칙이 있습니다.

**하나, 챗봇과 다른 계열 모델을 쓰세요.** LLM은 자기가 만들었을 법한 답을 좋게 평가하는 성향이 있습니다(5편에서 논문과 함께 자세히). 챗봇이 Claude면 judge는 GPT나 Gemini로, 같은 회사 모델이라도 최소한 다른 크기로 두세요.

**둘, 최상위 모델일 필요는 없습니다.** 채점은 생성보다 쉬운 작업이라 중간급 모델로도 충분한 경우가 많습니다. 다만 이건 **가정이 아니라 측정할 문제**입니다 — 4편에서 두 모델의 일치율을 재보고 결정하세요. 싼 모델이 사람과 잘 맞으면 그걸 쓰면 됩니다.

**셋, `temperature=0`** 으로 고정하세요. 같은 입력에 같은 판정이 나와야 합니다. 완전히 결정론적이진 않지만 흔들림이 크게 줍니다.

**비용 감각:** 케이스당 대화 맥락 2,000토큰 + 출력 300토큰 정도로 잡으면, 중간급 모델 기준 200건에 **몇백 원~2천 원** 수준입니다. 하루에 몇 번 돌려도 부담 없는 금액입니다.

## few-shot — 사람 라벨을 judge에게 보여주기

judge가 애매한 케이스에서 자꾸 틀린다면, **2편에서 모은 사람 라벨 몇 개를 rubric에 예시로 넣는 것**이 가장 효과가 큰 개선입니다.

```
## 판정 예시

[예시 1]
고객(로그인): 어제 주문한 거 아직도 안 왔어요
답변: 주문번호를 알려주시면 확인해 드릴게요!
→ FAIL. 조회 가능한 정보를 되물었다.

[예시 2]
고객: 산미 있는 원두 추천해주세요
답변: 에티오피아 예가체프 추천드려요! 자몽 같은 산미가 특징입니다.
→ PASS. 질문에 구체적으로 답했다.

[예시 3]
고객: 어제 받았는데 봉투가 터져서 왔어요
답변: 불편을 드려 죄송합니다. 고객센터로 문의해 주세요.
→ FAIL. 사과만 하고 조치를 떠넘겼다. (조건 3)
```

**어떤 걸 예시로 고를까요?** 명백한 케이스 말고 **경계에 있는 케이스**를 고르세요. "누가 봐도 FAIL"인 건 judge도 이미 맞힙니다. judge가 헷갈리는 지점을 예시로 못 박는 게 효과적입니다.

### ⚠️ 여기서 반드시 주의할 것

**예시로 쓴 케이스는 judge 검증에서 빼야 합니다.**

judge에게 "케이스 0042는 FAIL이야"라고 알려준 뒤, 케이스 0042로 judge를 시험하면 당연히 맞힙니다. **답을 알려주고 시험을 보는 것**이죠. 일치율이 부풀려집니다.

그래서 100개의 사람 라벨을 이렇게 나눕니다.

```
라벨 100개
   ├─ 60개  → judge 개발용 (few-shot 예시 뽑기, rubric 고치기)
   └─ 40개  → 검증용. judge에게 절대 보여주지 않음 (홀드아웃)
```

**홀드아웃(holdout)** 이라고 부르고, 4편에서 자세히 다룹니다. 지금은 "예시로 쓴 건 시험에서 뺀다"만 기억하세요.

## 흔한 실수 다섯 가지

**① rubric에 조건이 너무 많음.** 20개 조항을 넣으면 judge가 뒷부분을 흘립니다. **5~8개**가 적당하고, 그 이상이면 rubric을 두 개로 나누세요("정확성 judge"와 "말투 judge"처럼).

**② 하나의 judge로 여러 가지를 평가.** "정확하고, 친절하고, 간결한가?"를 한 번에 물으면 어느 축에서 실패했는지 알 수 없습니다. **축마다 judge를 따로** 두고 각각 PASS/FAIL을 받는 게 낫습니다.

**③ 정답 답변을 judge에게 주기.** "정답은 이것인데 이 답변이 맞나?"라고 물으면 judge가 표현 차이만으로 FAIL을 남발합니다. 정답이 하나가 아니라는 게 이 시리즈의 출발점이었죠.

**④ 판정 근거를 안 받음.** `verdict`만 받으면 나중에 왜 틀렸는지 분석할 수 없습니다. `findings`는 토큰을 조금 더 쓰지만 그 값을 합니다.

**⑤ rubric 버전을 기록 안 함.** rubric을 고치면 점수가 바뀝니다. **어느 rubric으로 잰 숫자인지 결과에 같이 저장**하세요. 안 그러면 3주 뒤에 "이 74%가 어느 기준이었지?"에 답을 못 합니다.

```json
{
  "case_id": "case-0042",
  "verdict": "FAIL",
  "rubric_version": "v3",
  "judge_model": "gpt-4.1-mini",
  "judged_at": "2026-07-31T16:00:00+09:00"
}
```

## 도구에서는 어떻게 부르나

- **promptfoo** — `assert: [{ type: llm-rubric, value: "..." }]`. rubric을 YAML에 문자열로 씁니다. 가장 빨리 시작할 수 있는 형태입니다.
- **DeepEval** — `GEval(criteria=..., evaluation_steps=[...])`. G-Eval 논문 구현이라 단계별 추론을 강제합니다.
- **Langfuse** — UI에서 evaluator를 만들고 프롬프트와 출력 스키마를 지정합니다.
- **autoevals** (Braintrust) — `LLMClassifier`. rubric + 선택지 매핑을 넘기면 됩니다.

어느 도구든 결국 **(rubric 프롬프트) + (출력 스키마) + (모델·온도 설정)** 세 조각입니다. 도구를 쓰든 직접 짜든 구조는 위 코드와 같습니다.

## 한 줄 정리

judge는 **rubric 프롬프트 한 장과 출력 스키마 하나**이며, rubric에는 **FAIL 조건을 번호로 구체적으로** 적고 **"평가하지 말 것"** 을 함께 명시합니다. 출력 스키마는 **근거(findings) → 추론 → 판정(verdict)** 순서여야 하고, few-shot 예시로 쓴 케이스는 **검증용에서 반드시 제외**해야 합니다.

---
← 이전: [2편. 사람이 먼저 채점한다](./02-human-labeling.md) | 다음: [4편. judge를 믿어도 되는가](./04-validate-the-judge.md) →
