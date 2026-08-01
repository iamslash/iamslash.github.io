# 7편. 논문과 오픈소스 — 더 공부할 거리

> 시리즈: AI 답변을 채점하는 법 — LLM-as-a-Judge 밑바닥부터
> 이 편에서 배우는 것: 반드시 읽어야 할 논문을 쉬운 것부터 순서대로, 직접 만들기 전에 가져다 쓸 오픈소스 도구, 그리고 상황별로 무엇부터 시작할지.

이 시리즈(0~6편)는 LLM-as-a-Judge의 **밑바닥 직관**을 다뤘습니다. 여기서 더 나아가고 싶은 분을 위해 정리했습니다.

> **어디까지 하면 되나:** **0~1단계면 실무 충분**, **2단계면 상급자**, **3단계는 그 상황이 실제로 닥쳤을 때** 파도 됩니다.

---

# 논문

## 0단계 · 반드시 읽을 세 편 🟢

이 셋만 읽어도 이 시리즈에서 다룬 내용의 학술적 근거를 다 잡습니다. 셋 다 무료입니다.

**① "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"**
Zheng et al., NeurIPS 2023 — [arXiv:2306.05685](https://arxiv.org/abs/2306.05685)

이 분야의 **기준 문헌**입니다. 여기서 시작하세요.

- **"judge가 옳다는 근거 = 사람과의 일치율"** 이라는 검증 방식을 정립했습니다. 우리 시리즈의 4편이 통째로 이 아이디어입니다.
- 강한 judge가 **사람끼리의 일치율에 준하는 수준**에 도달함을 보였습니다. 2편·4편에서 사람끼리의 일치율을 judge 평가의 기준점으로 삼은 근거입니다. (다만 이 논문도 그것을 넘을 수 없는 상한이라고 말하지는 않습니다 — 2편의 설명 상자 참고.)
- **position bias, verbosity bias, self-enhancement bias** 세 편향을 문서화했습니다. 5편의 대부분이 여기서 나옵니다.

읽기 팁: 전체가 길지만 **편향을 다루는 절만 읽어도 본전**입니다.

**② "G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment"**
Liu et al., EMNLP 2023 — [arXiv:2303.16634](https://arxiv.org/abs/2303.16634)

**평가 절차를 chain-of-thought로 먼저 쓰게 한 뒤 점수를 매기면 사람 판단과 더 잘 맞는다**는 것을 보인 논문입니다. 3편의 "근거를 먼저, 판정을 나중에"가 같은 방향입니다.

> **정확히 해두면:** 이 논문은 평가 절차를 CoT로 생성하고 form-filling(정해진 양식 채우기)으로 점수를 내는 방식을 실험한 것이지, **JSON 필드 순서를 실험한 것이 아닙니다.** 3편의 필드 순서 규칙은 자기회귀 생성이라는 성질에서 나온 것이고, 이 논문은 그 방향을 뒷받침하는 근거이지 직접적인 증명은 아닙니다.

DeepEval의 `GEval` 메트릭이 이 논문의 구현입니다.

**③ "Who Validates the Validators? Aligning LLM-Assisted Evaluation of LLM Outputs with Human Preferences"**
Shankar et al., UIST 2024 — [arXiv:2404.12272](https://arxiv.org/abs/2404.12272)

**실무자에게 가장 직접적으로 유용한 논문**입니다. 사람이 채점하면서 LLM 평가자를 정렬시키는 과정을 실제 사용자 연구로 관찰했습니다.

핵심 발견이 **criteria drift(기준 표류)** — 사람은 데이터를 보면서 자기 채점 기준이 계속 바뀝니다. 2편에서 "기준을 메모하면서 채점하고 끝나고 앞부분을 재채점하라"고 한 것의 근거입니다.

> **"평가 기준은 미리 정하는 게 아니라 데이터를 보면서 발견하는 것"** — 이 한 문장이 이 논문의 정수입니다.

## 1단계 · 편향을 깊게 🟢🟡

**④ "Large Language Models are not Fair Evaluators"**
Wang et al. — [arXiv:2305.17926](https://arxiv.org/abs/2305.17926) (2023 preprint), 최종 출판 ACL 2024

position bias를 정면으로 다룹니다. 순서만 바꿔도 승자가 뒤집히는 현상, 그리고 **순서를 교환해 두 번 물어본다**는 완화 아이디어가 여기서 나옵니다.

> **논문과 5편의 차이:** 논문의 방식(Balanced Position Calibration)은 두 순서의 **점수를 평균**냅니다. 5편의 `compare()`는 순서 교환이라는 아이디어만 빌려오되 **두 순서의 결론이 같을 때만 승자로 인정**하는 더 보수적인 규칙을 씁니다. 논문이 제시한 방법 중 하나가 아니라 **다른 정책**이라는 점을 구분해 두세요. 판정이 흔들린 케이스를 아예 무승부로 버리는 대신 확신도가 올라가는 맞바꿈입니다.

**⑤ "LLM Evaluators Recognize and Favor Their Own Generations"**
Panickssery et al., 2024 — [arXiv:2404.13076](https://arxiv.org/abs/2404.13076)

**LLM은 자기 출력을 어느 정도 알아보고 편애합니다.** 5편의 자기편애 편향이고, "judge 모델과 챗봇 모델을 다른 계열로 두라"는 권고의 근거입니다.

챗봇과 judge에 같은 모델을 쓰고 있다면 이 논문을 읽고 결정하세요.

**⑥ "A Survey on LLM-as-a-Judge"**
Gu et al., 2024 — [arXiv:2411.15594](https://arxiv.org/abs/2411.15594)

이 분야 전체를 훑는 서베이입니다. 개별 논문을 다 읽을 시간이 없다면 이걸로 지형을 파악하고, 관심 가는 것만 원문으로 가세요.

## 2단계 · 통계 기초 🟡

**⑦ "A Coefficient of Agreement for Nominal Scales"**
Jacob Cohen, 1960

4편에서 계산한 **Cohen's kappa의 원논문**입니다. 60년이 넘은 통계학 논문이고 짧습니다. LLM과 무관하게 "두 채점자가 얼마나 일치하는가"를 재는 표준이라, 한 번 읽어두면 평생 씁니다.

**⑧ "The Measurement of Observer Agreement for Categorical Data"**
Landis & Koch, 1977

4편의 κ 해석표(0.61~0.80 = "상당히 일치")가 여기서 나온 것입니다. **이게 법칙이 아니라 경험칙이라는 걸 확인하는 용도**로 보세요. 실무에서 이 표를 절대 기준처럼 쓰는 경우가 많은데, 원저자들도 그렇게 의도하지 않았습니다.

**⑨ McNemar 검정** *(논문이 아니라 개념 — 통계 교과서나 위키백과로 충분)*

6편의 짝비교가 이겁니다. "같은 대상을 두 방법으로 처리했을 때 차이가 진짜인가"를 재는 검정으로, A/B 테스트의 짝지어진 버전입니다. 원논문(McNemar, 1947)까지 갈 필요는 없습니다.

## 3단계 · 더 멀리 🔴

**⑩ "RAGAS: Automated Evaluation of Retrieval Augmented Generation"**
Es et al. — [arXiv:2309.15217](https://arxiv.org/abs/2309.15217) (2023 preprint), 최종 출판 EACL 2024 (시스템 데모)

RAG(검색 증강 생성) 시스템을 평가한다면 필독입니다. faithfulness(답변이 검색된 문서에 근거하는가), answer relevancy 같은 **RAG 전용 judge 지표**를 정의했습니다.

**⑪ "Can Large Language Models Be an Alternative to Human Evaluations?"**
Chiang & Lee, ACL 2023

LLM 평가가 사람 평가를 대체할 수 있는지를 초기에 검증한 논문. 지금 보면 결론이 익숙하지만, **어떤 조건에서 되고 안 되는지**를 나눠 본 게 좋습니다.

**⑫ 그 외 방향들** *(개별 논문 목록이 아니라, 필요해지면 이 키워드로 찾아보라는 안내)*
- **전용 judge 모델 학습** — 범용 LLM 대신 평가만 하도록 파인튜닝한 모델(JudgeLM, PandaLM, Prometheus 계열). 평가 볼륨이 아주 크고 비용이 문제일 때 봅니다.
- **rubric 자동 생성** — 사람 라벨에서 rubric을 역으로 뽑아내는 연구. Shankar 등의 EvalGen이 그 방향입니다.
- **Elo / Bradley-Terry** — Chatbot Arena가 pairwise 승패를 순위로 바꾸는 방식. 프롬프트 후보가 2개가 아니라 10개일 때 필요합니다.

---

# 오픈소스

## 0단계 · 오늘 당장 시작하기 🟢

**promptfoo** — [github.com/promptfoo/promptfoo](https://github.com/promptfoo/promptfoo)

**처음이라면 여기서 시작하세요.** CLI + YAML이라 30분이면 첫 실행이 됩니다.

```yaml
prompts:
  - file://prompts/v1.txt
  - file://prompts/v2.txt      # 두 프롬프트를 나란히

providers:
  - openai:gpt-4.1-mini

tests:
  - vars:
      conversation: "어제 주문한 거 아직도 안 왔어요"
      logged_in: true
    assert:
      - type: llm-rubric
        value: |
          로그인 고객에게 주문번호를 되물으면 실패다.
          조회 가능한 정보를 스스로 안내했으면 통과다.
```

`npx promptfoo eval` 하면 격자표로 결과가 뜹니다. **6편의 2~3단계를 그대로 해줍니다.** `select-best` assertion으로 pairwise도 됩니다.

**scikit-learn** — 4편의 검증 계산

```python
from sklearn.metrics import cohen_kappa_score, confusion_matrix, classification_report
```

4편에서 손으로 짠 코드를 대체합니다. 실무에서는 이걸 쓰세요. McNemar는 `statsmodels`에 있습니다.

## 1단계 · 루프를 제대로 돌리기 🟢🟡

**Langfuse** — [github.com/langfuse/langfuse](https://github.com/langfuse/langfuse)

**이 시리즈 전체를 한 제품에 담은 것에 가장 가깝습니다.** 오픈소스(자체 호스팅 가능)이고, 다음이 다 들어 있습니다.

- **Dataset** — 1편의 테스트 케이스
- **Annotation Queue** — 2편의 사람 채점
- **LLM-as-a-judge Evaluator** — 3편의 judge
- **Experiment** — 6편의 프롬프트 버전별 비교
- **Prompt Management** — 프롬프트 버전 관리 (어느 버전으로 잰 숫자인지 자동 기록)

**"우리 조직에 평가 체계를 세우자"** 단계라면 이걸 먼저 보고, 부족한 부분만 직접 만드는 게 효율적입니다. 다만 4편의 κ 계산은 여기서도 직접 해야 합니다.

**Argilla** — [github.com/argilla-io/argilla](https://github.com/argilla-io/argilla)

라벨링 **전용** 오픈소스. 2편의 사람 채점 UI가 가장 잘 만들어져 있습니다. 여러 명이 나눠서 대량으로 라벨링해야 한다면 이쪽입니다.

**DeepEval** — [github.com/confident-ai/deepeval](https://github.com/confident-ai/deepeval)

pytest처럼 쓰는 파이썬 평가 라이브러리.

```python
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

metric = GEval(
    name="상담 품질",
    criteria="로그인 고객에게 조회 가능한 정보를 되묻지 않았는가",
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
)
```

> DeepEval은 버전에 따라 파라미터 이름과 import 경로가 바뀌어 왔습니다. **설치한 버전의 문서를 확인**하세요 — 위 코드는 형태를 보여주기 위한 것입니다.

**CI에 평가를 붙이고 싶을 때** 가장 자연스럽습니다. `pytest`로 돌아가니 기존 테스트 파이프라인에 그대로 들어갑니다. G-Eval 구현이 들어 있는 것도 장점.

**Ragas** — [github.com/explodinggradients/ragas](https://github.com/explodinggradients/ragas)

RAG 전용. 문서 검색이 들어간 챗봇이라면 여기 지표들(faithfulness, context precision 등)을 먼저 보세요. 직접 rubric을 쓰는 것보다 낫습니다.

## 2단계 · 참조 구현과 관측 🟡

**FastChat의 `llm_judge`** — [github.com/lm-sys/FastChat](https://github.com/lm-sys/FastChat) (`fastchat/llm_judge/`)

MT-Bench 논문의 **실제 코드**입니다. 특히 **position bias를 순서 교환으로 처리하는 부분**이 그대로 들어 있어서, 5편의 `compare()`를 직접 구현하기 전에 한 번 읽어보면 좋습니다. 도입용이 아니라 참고용.

**Arize Phoenix** — [github.com/Arize-ai/phoenix](https://github.com/Arize-ai/phoenix)
**Opik** (Comet) — [github.com/comet-ml/opik](https://github.com/comet-ml/opik)

관측(tracing)과 평가를 함께 다루는 오픈소스들. 이미 LLM 앱의 trace를 수집하고 있다면 그 위에 평가를 얹는 형태라 자연스럽습니다.

**autoevals** — [github.com/braintrustdata/autoevals](https://github.com/braintrustdata/autoevals)

judge 채점기 모음 라이브러리. `LLMClassifier`(pointwise), `Battle`(pairwise) 등이 있어서 **함수 하나만 가져다 쓰기 좋습니다.**

**LangSmith** (상용) — 이미 LangChain 계열을 쓰고 있다면 자연스러운 선택. annotation queue와 evaluator가 trace에 붙어 있습니다. 오픈소스는 아닙니다.

## 3단계 · 벤치마크·연구용 🔴

**Inspect AI** — [github.com/UKGovernmentBEIS/inspect_ai](https://github.com/UKGovernmentBEIS/inspect_ai)
영국 AI Safety Institute가 만든 평가 프레임워크. 모델 안전성 평가 쪽에서 표준처럼 쓰입니다. **제품 평가보다 모델 평가에 어울립니다.**

**OpenAI Evals** — [github.com/openai/evals](https://github.com/openai/evals)
초창기 프레임워크. 지금은 위 도구들이 더 편하지만, 레지스트리 구조를 참고할 만합니다.

**ChainForge** — [github.com/ianarawjo/ChainForge](https://github.com/ianarawjo/ChainForge)
프롬프트 실험을 시각적으로 하는 도구. Shankar 등의 **EvalGen 프로토타입**이 여기 들어 있어서, 논문 ③을 읽었다면 실물을 볼 수 있습니다.

---

# 실무자 글

논문보다 이쪽이 더 도움 될 수 있습니다. 전부 무료입니다.

- **Hamel Husain — "Your AI Product Needs Evals"**, **"Creating a LLM-as-a-Judge That Drives Business Results"**
  이 주제의 **실무 교본**에 가깝습니다. "데이터를 봐라", "도메인 전문가 한 명이 기준을 잡아라", "이진 판정을 써라" — 이 시리즈 2편의 뼈대가 여기서 왔습니다.

- **Eugene Yan — "Task-Specific LLM Evals that Do & Don't Work"**
  어떤 평가가 실제로 작동하고 어떤 게 안 되는지를 사례로 정리했습니다.

- **Shreya Shankar의 블로그** — 논문 ③의 저자. 평가 도구를 만들면서 겪은 실무 이야기가 많습니다.

---

# 상황별 출발점

**"일단 뭐라도 시작하고 싶다"**
→ 대화 로그 50개를 스프레드시트에 붙여놓고 직접 PASS/FAIL을 매기세요. 도구도 코드도 필요 없습니다. **이 시리즈에서 가장 가치 있는 한 시간**이 될 겁니다. (2편)

**"프롬프트 두 개 중 뭐가 나은지만 알고 싶다"**
→ promptfoo. 반나절. (6편 + promptfoo)

**"CI에 회귀 검사를 붙이고 싶다"**
→ DeepEval + pytest. (3편의 rubric을 그대로 옮기면 됩니다)

**"조직에 평가 체계를 세우고 싶다"**
→ Langfuse를 먼저 띄워보고, 부족한 부분(κ 계산, 짝비교)만 노트북으로 채우세요.

**"judge가 못 미덥다"**
→ 논문 ①⑤를 읽고, 4편의 검증을 judge 모델을 바꿔가며 해보세요.

---

# 마지막 한마디

새 기법을 많이 아는 것보다 **두 가지가 훨씬 중요합니다.**

**하나, 데이터를 직접 보는 것.** 로그 50개를 읽으면 rubric에 뭘 써야 할지 알게 됩니다. 안 읽고 상상으로 쓴 rubric은 현실에 없는 문제를 잡습니다. 이 시리즈에서 딱 하나만 가져가신다면 이것입니다.

**둘, 자를 검증하는 것.** judge를 만드는 데 하루, 검증하는 데 하루를 쓰면 그 judge는 몇 달을 씁니다. 검증을 건너뛰고 만든 judge는 **틀린 방향으로 몇 달을 달리게 만듭니다.**

화려한 기법(전용 judge 모델, Elo 순위, 자동 rubric 생성)은 **특정 상황용 20%** 이고, 실전 가치의 **80%는 "사람이 직접 본 라벨 100개 + 그걸로 검증한 judge"** 에서 나옵니다.

---
← 이전: [6편. 프롬프트 A와 B, 어느 쪽이 나은가](./06-ab-loop.md)
