---
name: test-driven-development
description: 모든 기능 구현이나 버그 수정 시, 구현 코드를 작성하기 전에 사용할 것
---

# 테스트 주도 개발 (TDD)

## 개요

테스트를 먼저 작성하라. 실패하는 것을 확인하라. 통과시킬 최소한의 코드를 작성하라.

**핵심 원칙:** 테스트가 실패하는 것을 직접 보지 않았다면, 그 테스트가 올바른 것을 검증하는지 알 수 없다.

**규칙의 문자(letter)를 어기는 것은 곧 규칙의 정신(spirit)을 어기는 것이다.**

## 사용 시점

**항상:**
- 새로운 기능
- 버그 수정
- 리팩터링
- 동작(behavior) 변경

**예외 (사람 파트너에게 물어볼 것):**
- 일회성 프로토타입
- 자동 생성된 코드
- 설정(configuration) 파일

"이번 한 번만 TDD를 건너뛸까?"라고 생각하고 있는가? 멈춰라. 그건 합리화다.

## 철의 법칙 (The Iron Law)

```
실패하는 테스트가 먼저 존재하지 않는 한, 프로덕션 코드를 작성하지 않는다
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

테스트보다 먼저 코드를 작성했다면? 삭제하라. 처음부터 다시 시작하라.

**예외 없음:**
- "참고용"으로 남겨두지 말 것
- 테스트를 쓰면서 그 코드를 "각색(adapt)"하지 말 것
- 그 코드를 쳐다보지도 말 것
- 삭제는 진짜 삭제를 의미한다

테스트로부터 새롭게(fresh) 구현하라. 그게 전부다.

## Red-Green-Review

> **Human-in-the-Loop 원칙**: RED와 REVIEW 단계는 반드시 사람의 검토를 거쳐야 한다.
> 사람의 승인 없이 이 두 단계를 넘어가는 것은 절대 금지다.

```dot
digraph tdd_cycle {
    rankdir=LR;
    plan [label="PLAN\n테스트 계획 작성\n(Plan.md)", shape=box, style=filled, fillcolor="#ffe0b2"];
    human_red [label="사람 검토\n(RED 승인)", shape=diamond, style=filled, fillcolor="#ff9800"];
    red [label="RED\n실패하는 테스트 작성", shape=box, style=filled, fillcolor="#ffcccc"];
    verify_red [label="제대로\n실패하는지 확인", shape=diamond];
    green [label="GREEN\n최소한의 코드", shape=box, style=filled, fillcolor="#ccffcc"];
    verify_green [label="통과 확인\n전체 그린", shape=diamond];
    review [label="REVIEW\n코드 검토", shape=box, style=filled, fillcolor="#ccccff"];
    human_review [label="사람 검토\n(REVIEW 승인)", shape=diamond, style=filled, fillcolor="#ff9800"];
    next [label="다음 싸이클", shape=ellipse];

    plan -> human_red;
    human_red -> red [label="승인"];
    human_red -> plan [label="수정 필요"];
    red -> verify_red;
    verify_red -> green [label="예"];
    verify_red -> red [label="잘못된\n실패"];
    green -> verify_green;
    verify_green -> review [label="예"];
    verify_green -> green [label="아니오"];
    review -> human_review;
    human_review -> next [label="승인"];
    human_review -> review [label="수정 필요"];
    next -> plan;
}
```

### RED - 테스트 작성 계획 및 검토

**⚠️ 사람의 검토 없이 이 단계를 넘어가면 안 된다.**

#### 1단계: Plan.md 작성

테스트를 작성하기 전에 `Plan.md`를 먼저 작성하라.

**Plan.md 포함 내용:**
- 이번 싸이클에서 검증할 동작(behavior)
- 테스트 케이스 이름과 시나리오
- 예상 입력/출력
- 엣지 케이스 목록
- 구현하지 않을 범위 (Out of Scope)

**예시 Plan.md:**
```markdown
## 테스트 계획: 거터 게임

### 검증할 동작
모든 투구에서 핀을 하나도 쓰러뜨리지 못할 때 총점이 0이어야 한다.

### 테스트 케이스
- `test_gutter_game`: 20번 투구 모두 0핀 → 총점 0

### 예상 입력/출력
- 입력: roll(0) × 20
- 출력: score() == 0

### 엣지 케이스
- 해당 없음 (단순 케이스)

### Out of Scope
- 유효하지 않은 핀 수 검증
```

#### 2단계: 사람 검토 요청

Plan.md 작성 후 반드시 사람에게 검토를 요청하라:

```
Plan.md를 작성했습니다. 검토해 주세요.
[Plan.md 내용 요약]
승인하시면 테스트 코드를 작성하겠습니다.
```

**사람의 승인 전까지 테스트 코드를 작성하지 말 것.**

#### 3단계: 테스트 작성 (승인 후)

무엇이 일어나야 하는지를 보여주는 최소한의 테스트 한 개를 작성하라.

<Good>
```python
def test_retries_failed_operations_3_times():
    attempts = 0

    def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError("fail")
        return "success"

    result = retry_operation(operation)

    assert result == "success"
    assert attempts == 3
```
명확한 이름, 실제 동작 검증, 한 가지만 검증
</Good>

<Bad>
```python
def test_retry_works(mocker):
    mock = mocker.Mock(side_effect=[RuntimeError(), RuntimeError(), "success"])
    retry_operation(mock)
    assert mock.call_count == 3
```
모호한 이름, 실제 코드가 아닌 mock을 검증
</Bad>

**요건:**
- 하나의 동작(behavior)
- 명확한 이름
- 실제 코드 (불가피한 경우가 아니면 mock 사용 금지)

### RED 검증 - 실패하는 것을 직접 보기

**필수. 절대 건너뛰지 말 것.**

```bash
pytest path/to/test_file.py
```

다음을 확인하라:
- 테스트가 실패한다 (에러가 아니라)
- 실패 메시지가 예상한 그대로다
- 기능이 없어서 실패한다 (오타 때문이 아니라)

**테스트가 통과한다고?** 이미 존재하는 동작을 검증하고 있는 것이다. 테스트를 고쳐라.

**테스트가 에러를 낸다고?** 에러를 고치고, 제대로 실패할 때까지 다시 실행하라.

### GREEN - 최소한의 코드

테스트를 통과시키는 가장 단순한 코드를 작성하라.

<Good>
```python
def retry_operation(fn):
    for i in range(3):
        try:
            return fn()
        except Exception as e:
            if i == 2:
                raise
    raise RuntimeError("unreachable")
```
통과시킬 만큼만
</Good>

<Bad>
```python
def retry_operation(
    fn,
    max_retries=3,
    backoff="linear",  # "linear" | "exponential"
    on_retry=None,
):
    # YAGNI (You Aren't Gonna Need It)
    ...
```
과도한 설계
</Bad>

기능을 추가하지 말고, 다른 코드를 리팩터링하지 말고, 테스트가 요구하는 것 이상으로 "개선"하지 말라.

### GREEN 검증 - 통과하는 것을 직접 보기

**필수.**

```bash
pytest path/to/test_file.py
```

다음을 확인하라:
- 테스트가 통과한다
- 다른 테스트들도 여전히 통과한다
- 출력이 깨끗하다 (에러, 경고 없음)

**테스트가 실패한다?** 테스트가 아니라 코드를 고쳐라.

**다른 테스트가 실패한다?** 지금 당장 고쳐라.

### REVIEW - 코드 검토 및 사람 승인

**⚠️ 사람의 검토 없이 다음 싸이클로 넘어가면 안 된다.**

GREEN이 된 코드를 검토하라:
- 중복 제거가 필요한가?
- 이름 개선이 필요한가?
- 헬퍼(helper) 추출이 필요한가?
- 다음 싸이클에서 다룰 동작은 무엇인가?

필요한 정리 작업을 수행한 뒤, 반드시 사람에게 검토를 요청하라:

```
REVIEW 단계가 완료되었습니다. 검토해 주세요.

[이번 싸이클 요약]
- 구현한 동작:
- 작성/수정한 코드:
- 정리한 내용:

[다음 싸이클 제안]
- 다음에 다룰 동작:

승인하시면 다음 싸이클의 Plan.md를 작성하겠습니다.
```

**사람의 승인 전까지 다음 싸이클을 시작하지 말 것.**

### 반복

사람의 승인 후, 다음 기능에 대한 Plan.md를 작성하라.

## 좋은 테스트

| 품질 | 좋음 | 나쁨 |
|------|------|------|
| **최소성** | 한 가지만 검증. 이름에 "and"가 들어가는가? 분리하라. | `test_validates_email_and_domain_and_whitespace` |
| **명확성** | 이름이 동작을 설명한다 | `test_test1` |
| **의도 표현** | 원하는 API를 보여준다 | 코드가 무엇을 해야 하는지 가린다 |

## 왜 순서가 중요한가

**"코드를 먼저 짜고 나중에 테스트로 검증할게요"**

코드 이후에 작성된 테스트는 즉시 통과한다. 즉시 통과한다는 것은 아무것도 증명하지 못한다:
- 잘못된 것을 검증하고 있을 수 있다
- 동작이 아니라 구현(implementation)을 검증하고 있을 수 있다
- 잊어버린 엣지 케이스를 놓쳤을 수 있다
- 그 테스트가 버그를 잡는 것을 한 번도 보지 못했다

테스트 우선(test-first)은 테스트가 실패하는 것을 강제로 보게 함으로써, 그 테스트가 실제로 무언가를 검증하고 있음을 증명한다.

**"이미 모든 엣지 케이스를 수동으로 테스트했어요"**

수동 테스트는 임시방편(ad-hoc)이다. 모든 것을 테스트했다고 생각하지만:
- 무엇을 테스트했는지 기록이 없다
- 코드가 변경될 때 다시 실행할 수 없다
- 압박 상황에서 케이스를 잊기 쉽다
- "내가 해봤을 때는 됐어요" ≠ 포괄적

자동화된 테스트는 체계적이다. 매번 동일한 방식으로 실행된다.

**"X시간 작업한 걸 지우는 건 낭비예요"**

매몰비용(sunk cost) 오류다. 시간은 이미 지나갔다. 지금 당신의 선택지는:
- 삭제하고 TDD로 다시 작성 (X시간 더, 높은 확신)
- 그대로 두고 나중에 테스트 추가 (30분, 낮은 확신, 버그 가능성 큼)

진짜 "낭비"는 신뢰할 수 없는 코드를 유지하는 것이다. 진짜 테스트가 없는 동작 코드는 기술 부채다.

**"TDD는 교조적이에요. 실용적이라는 건 상황에 맞게 조정하는 것"**

TDD가 바로 실용적이다:
- 커밋 전에 버그를 발견 (나중에 디버깅하는 것보다 빠름)
- 회귀(regression) 방지 (테스트가 깨짐을 즉시 잡아냄)
- 동작을 문서화 (테스트가 코드 사용법을 보여줌)
- 자유로운 리팩터링 가능 (마음껏 바꿔도 테스트가 깨짐을 잡음)

"실용적"이라는 이름의 지름길 = 프로덕션에서의 디버깅 = 더 느리다.

**"테스트를 나중에 써도 같은 목표를 달성해요 - 정신이 중요하지 의식이 중요한 게 아니에요"**

아니다. 사후(after) 테스트는 "이 코드가 무엇을 하는가?"에 답한다. 사전(first) 테스트는 "이 코드가 무엇을 해야 하는가?"에 답한다.

사후 테스트는 당신의 구현에 편향(bias)되어 있다. 요구되는 것이 아니라 당신이 만든 것을 검증한다. 발견된 엣지 케이스가 아니라 당신이 기억하는 엣지 케이스를 검증한다.

사전 테스트는 구현 전에 엣지 케이스 발견을 강제한다. 사후 테스트는 당신이 모든 것을 기억했는지 검증한다 (당신은 기억하지 못했다).

사후에 30분 동안 테스트를 쓰는 것 ≠ TDD. 커버리지는 얻지만, 테스트가 작동한다는 증명은 잃는다.

## 흔한 합리화들

| 변명 | 현실 |
|------|------|
| "너무 단순해서 테스트할 게 없어요" | 단순한 코드도 깨진다. 테스트는 30초면 쓴다. |
| "나중에 테스트할게요" | 즉시 통과하는 테스트는 아무것도 증명하지 않는다. |
| "사후 테스트도 같은 목표 달성" | 사후 = "무엇을 하는가?" 사전 = "무엇을 해야 하는가?" |
| "이미 수동으로 테스트했어요" | 임시방편 ≠ 체계적. 기록 없음, 재실행 불가. |
| "X시간 작업 지우는 건 낭비" | 매몰비용 오류. 미검증 코드 유지가 기술 부채. |
| "참고용으로 두고 테스트부터" | 결국 그 코드를 각색하게 된다. 그게 사후 테스트다. 삭제는 진짜 삭제다. |
| "먼저 탐색(explore)이 필요해요" | 좋다. 탐색물은 버리고, TDD로 시작하라. |
| "테스트가 어렵다는 건 설계가 불명확하다는 뜻" | 테스트의 말을 들어라. 테스트하기 어려우면 사용하기도 어렵다. |
| "TDD는 나를 느리게 해요" | TDD가 디버깅보다 빠르다. 실용적 = 테스트 우선. |
| "수동 테스트가 더 빨라요" | 수동은 엣지 케이스를 증명하지 못한다. 매번 다시 테스트해야 한다. |
| "기존 코드엔 테스트가 없어요" | 당신이 그 코드를 개선하는 중이다. 기존 코드에 대한 테스트도 추가하라. |
| "Plan.md 없이 바로 시작하면 안 돼요?" | 안 된다. Plan.md는 사람과의 합의 도구다. 건너뛰는 순간 human-in-the-loop가 무너진다. |

## 위험 신호 (Red Flags) - 멈추고 처음부터

- 테스트보다 코드가 먼저 있다
- 구현 후에 테스트를 쓴다
- 테스트가 즉시 통과한다
- 왜 테스트가 실패했는지 설명할 수 없다
- 테스트를 "나중에" 추가한다
- "이번 한 번만"이라고 합리화한다
- "이미 수동으로 테스트했어요"
- "사후 테스트도 같은 목적을 달성해요"
- "정신이 중요하지 의식이 중요한 게 아니에요"
- "참고용으로 두고" 또는 "기존 코드 각색"
- "이미 X시간 썼는데, 지우는 건 낭비"
- "TDD는 교조적, 나는 실용적"
- "이건 다른 경우인데..."
- **Plan.md 없이 테스트를 작성했다**
- **사람 검토 없이 RED 단계를 넘어갔다**
- **사람 검토 없이 REVIEW 단계를 넘어갔다**

**이 모든 것은 다음을 의미한다: 코드를 삭제하라. TDD로 다시 시작하라.**

## 예시: 버그 수정

**버그:** 빈 이메일이 허용됨

**PLAN (Plan.md 작성 후 사람 검토 요청)**
```markdown
## 테스트 계획: 빈 이메일 거부

### 검증할 동작
빈 이메일로 폼을 제출하면 에러 메시지를 반환해야 한다.

### 테스트 케이스
- `test_rejects_empty_email`: email="" → {"error": "Email required"}

### 예상 입력/출력
- 입력: submit_form({"email": ""})
- 출력: result["error"] == "Email required"
```
→ **사람 검토 및 승인 대기**

**RED (승인 후 테스트 작성)**
```python
def test_rejects_empty_email():
    result = submit_form({"email": ""})
    assert result["error"] == "Email required"
```

**RED 검증**
```bash
$ pytest
FAILED: KeyError: 'error'   (또는 'Email required'를 기대했으나 다른 값)
```

**GREEN**
```python
def submit_form(data):
    email = data.get("email", "")
    if not email.strip():
        return {"error": "Email required"}
    # ...
```

**GREEN 검증**
```bash
$ pytest
PASSED
```

**REVIEW (코드 검토 후 사람 검토 요청)**
```
REVIEW 단계가 완료되었습니다. 검토해 주세요.

이번 싸이클 요약:
- 구현한 동작: 빈 이메일 제출 시 에러 반환
- 작성/수정한 코드: submit_form() 함수에 이메일 공백 검증 추가
- 정리한 내용: 특이사항 없음

다음 싸이클 제안:
- 공백만 있는 이메일(예: "   ") 처리

승인하시면 다음 싸이클의 Plan.md를 작성하겠습니다.
```
→ **사람 검토 및 승인 대기**

## 검증 체크리스트

작업을 완료(complete)로 표시하기 전에:

- [ ] Plan.md를 작성하고 사람의 승인을 받았다
- [ ] 모든 새 함수/메서드에 테스트가 있다
- [ ] 각 테스트가 실패하는 것을 직접 보고 구현했다
- [ ] 각 테스트가 예상한 이유로 실패했다 (오타가 아니라 기능 부재로)
- [ ] 각 테스트를 통과시키는 최소한의 코드를 작성했다
- [ ] 모든 테스트가 통과한다
- [ ] 출력이 깨끗하다 (에러, 경고 없음)
- [ ] 테스트가 실제 코드를 사용한다 (mock은 불가피할 때만)
- [ ] 엣지 케이스와 에러 케이스가 커버되어 있다
- [ ] REVIEW 단계에서 사람의 승인을 받았다

체크박스를 모두 채울 수 없다면? TDD를 건너뛴 것이다. 처음부터 다시 시작하라.

## 막혔을 때

| 문제 | 해결 |
|------|------|
| 어떻게 테스트할지 모르겠다 | 원하는 API를 먼저 적어보라. assertion부터 작성하라. 사람 파트너에게 물어보라. |
| 테스트가 너무 복잡하다 | 설계가 너무 복잡하다. 인터페이스를 단순화하라. |
| 모든 것을 mock해야 한다 | 코드가 너무 결합(coupled)되어 있다. 의존성 주입(DI)을 사용하라. |
| 테스트 셋업이 거대하다 | 헬퍼를 추출하라. 그래도 복잡하면 설계를 단순화하라. |
| Plan.md를 어떻게 써야 할지 모르겠다 | 검증할 동작을 한 문장으로 적는 것부터 시작하라. 사람 파트너에게 물어보라. |

## 디버깅 통합

버그를 발견했는가? 그 버그를 재현하는 실패하는 테스트를 먼저 작성하라. TDD 사이클을 따르라. 그 테스트가 수정을 증명하고 회귀를 방지한다.

테스트 없이 버그를 수정하지 말라.

## 테스트 안티패턴

mock이나 테스트 유틸리티를 추가할 때, @testing-anti-patterns.md 를 읽어 흔한 함정을 피하라:
- 실제 동작 대신 mock 동작을 테스트하기
- 프로덕션 클래스에 테스트 전용 메서드를 추가하기
- 의존성을 이해하지 못한 채 mock하기

## pytest 관련 추가 팁 (Python 특화)

### 픽스처(Fixtures)는 절제해서 사용하라

```python
# 좋음: 분명히 재사용되는 셋업만 픽스처로
@pytest.fixture
def temp_db():
    db = create_in_memory_db()
    yield db
    db.close()

def test_user_creation(temp_db):
    user = create_user(temp_db, name="Alice")
    assert user.id is not None
```

픽스처가 너무 많아지면 테스트의 의도가 흐려진다. 단순한 셋업은 테스트 안에 그대로 두는 편이 명확할 때가 많다.

### parametrize는 같은 동작의 여러 입력에만 사용하라

```python
# 좋음: 같은 동작 규칙, 여러 입력
@pytest.mark.parametrize("email", ["", "   ", "\t\n"])
def test_rejects_blank_email(email):
    result = submit_form({"email": email})
    assert result["error"] == "Email required"
```

서로 다른 동작을 parametrize로 묶지 말라. 그건 테스트 한 개가 아니라 여러 개로 나뉘어야 한다.

### mock은 외부 경계에서만

`unittest.mock` 또는 `pytest-mock`의 `mocker`를 쓸 때는, 우리가 제어할 수 없는 경계(네트워크, 파일시스템, 시간 등)에서만 사용하라. 우리 코드 내부 모듈 사이의 호출을 mock하기 시작했다면, 결합도가 너무 높다는 신호다.

### 테스트 실행 명령

```bash
# 단일 파일
pytest path/to/test_file.py

# 단일 테스트
pytest path/to/test_file.py::test_specific_case

# 첫 실패에서 멈춤 (빠른 RED 확인용)
pytest -x

# 자세한 출력
pytest -v

# 출력(print) 캡처 끔 (디버깅용)
pytest -s
```

## 최종 규칙

```
프로덕션 코드 → Plan.md 승인 + 테스트가 존재하고, 먼저 실패했다
다음 싸이클 → REVIEW 승인을 받았다
그 외 → TDD가 아니다
```

사람 파트너의 허가 없이는 예외 없음.
