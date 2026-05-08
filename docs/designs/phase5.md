# Phase 5 세부 설계 — OrderController (승인·재고 분기)

> TDD 순서: 테스트 작성(Red) → 구현(Green) → 전체 테스트 통과 확인 → 리팩토링 → 전체 테스트 통과 확인

---

## 대상 파일

| 구분 | 파일 |
|------|------|
| 구현 | `controllers/order_controller.py` (`approve` 메서드 추가) |
| 테스트 | `tests/test_order_controller.py` (케이스 추가) |

> Phase 4에서 구현한 `reserve` / `list_reserved` / `reject`는 변경하지 않는다.

---

## 역할 및 의존성 추가

```
OrderController.approve
    │
    ├── OrderRepository    (주문 조회·저장)
    ├── SampleRepository   (시료 재고 확인)
    └── ProductionRepository (생산 큐 등록)  ← Phase 5에서 새로 추가
```

---

## 핵심 비즈니스 로직

### 재고 분기

```
stock = sample.stock

if stock >= order.quantity:          # 재고 충분
    order.status = CONFIRMED

else:                                # 재고 부족
    shortage   = order.quantity - stock
    actual     = ceil(shortage / (sample.yield_rate * 0.9))
    total_time = sample.avg_production_time * actual
    생산 큐에 ProductionJob 추가
    order.status = PRODUCING
```

### 생산량 계산 공식

```
actual_production = ceil(부족분 / (yield_rate × 0.9))
total_time        = avg_production_time × actual_production
```

| 예시 | 값 |
|------|-----|
| 주문 수량 | 10 |
| 현재 재고 | 3 |
| 부족분 | 7 |
| yield_rate | 0.9 |
| actual_production | `ceil(7 / (0.9 × 0.9))` = `ceil(7 / 0.81)` = `ceil(8.64...)` = **9** |
| avg_production_time | 2.0 |
| total_time | 2.0 × 9 = **18.0** |

---

## Step 1 — 테스트 작성 (Red)

`tests/test_order_controller.py`에 아래 클래스를 추가한다.

```python
import math
from repositories.production_repository import ProductionRepository


@pytest.fixture
def ctrl_full(tmp_path):
    """approve 테스트용 — ProductionRepository 포함"""
    sample_repo     = SampleRepository(tmp_path / "samples.json")
    order_repo      = OrderRepository(tmp_path / "orders.json")
    production_repo = ProductionRepository(tmp_path / "production_queue.json")
    sample_repo.save(Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=0.9))
    return OrderController(
        sample_repo=sample_repo,
        order_repo=order_repo,
        production_repo=production_repo,
    )


# ── approve (재고 충분) ───────────────────────────────────────
class TestApproveWithSufficientStock:
    def test_status_becomes_confirmed(self, ctrl_full, tmp_path):
        # 재고 10, 주문 5 → 충분
        sample_repo = SampleRepository(tmp_path / "samples.json")
        sample = sample_repo.find_by_id("S001")
        sample.stock = 10
        sample_repo.save(sample)
        order = ctrl_full.reserve(sample_id="S001", customer="홍길동", quantity=5)
        ctrl_full.approve(order.order_id)
        updated = ctrl_full._order_repo.find_by_id(order.order_id)
        assert updated.status == OrderStatus.CONFIRMED

    def test_production_queue_remains_empty(self, ctrl_full, tmp_path):
        sample_repo = SampleRepository(tmp_path / "samples.json")
        sample = sample_repo.find_by_id("S001")
        sample.stock = 10
        sample_repo.save(sample)
        order = ctrl_full.reserve(sample_id="S001", customer="홍길동", quantity=5)
        ctrl_full.approve(order.order_id)
        queue = ctrl_full._production_repo.load()
        assert queue.is_empty()


# ── approve (재고 부족) ───────────────────────────────────────
class TestApproveWithInsufficientStock:
    def test_status_becomes_producing(self, ctrl_full):
        # 재고 0 (기본값), 주문 10 → 부족
        order = ctrl_full.reserve(sample_id="S001", customer="홍길동", quantity=10)
        ctrl_full.approve(order.order_id)
        updated = ctrl_full._order_repo.find_by_id(order.order_id)
        assert updated.status == OrderStatus.PRODUCING

    def test_production_job_added_to_queue(self, ctrl_full):
        order = ctrl_full.reserve(sample_id="S001", customer="홍길동", quantity=10)
        ctrl_full.approve(order.order_id)
        queue = ctrl_full._production_repo.load()
        assert queue.size() == 1
        assert queue.peek().order_id == order.order_id

    def test_actual_production_calculation(self, ctrl_full):
        # 부족분=10, yield_rate=0.9 → ceil(10 / 0.81) = ceil(12.34) = 13
        order = ctrl_full.reserve(sample_id="S001", customer="홍길동", quantity=10)
        ctrl_full.approve(order.order_id)
        job = ctrl_full._production_repo.load().peek()
        expected = math.ceil(10 / (0.9 * 0.9))
        assert job.actual_production == expected

    def test_total_time_calculation(self, ctrl_full):
        order = ctrl_full.reserve(sample_id="S001", customer="홍길동", quantity=10)
        ctrl_full.approve(order.order_id)
        job = ctrl_full._production_repo.load().peek()
        expected_actual = math.ceil(10 / (0.9 * 0.9))
        assert job.total_time == 2.0 * expected_actual

    def test_approve_nonexistent_order_raises(self, ctrl_full):
        with pytest.raises(ValueError):
            ctrl_full.approve("NONEXISTENT")
```

---

## Step 2 — 구현 (Green)

### `controllers/order_controller.py` — `approve` 추가

```python
import math

class OrderController:
    def __init__(self, sample_repo, order_repo, production_repo=None):
        self._sample_repo     = sample_repo
        self._order_repo      = order_repo
        self._production_repo = production_repo

    # ... (기존 reserve, list_reserved, reject 유지)

    def approve(self, order_id: str) -> None:
        order = self._order_repo.find_by_id(order_id)
        if order is None:
            raise ValueError(f"존재하지 않는 주문입니다: {order_id}")
        sample = self._sample_repo.find_by_id(order.sample_id)

        if sample.stock >= order.quantity:
            order.status = OrderStatus.CONFIRMED
            self._order_repo.save(order)
        else:
            shortage   = order.quantity - sample.stock
            actual     = math.ceil(shortage / (sample.yield_rate * 0.9))
            total_time = sample.avg_production_time * actual
            job = ProductionJob(
                order_id=order.order_id,
                sample_id=order.sample_id,
                actual_production=actual,
                total_time=total_time,
            )
            queue = self._production_repo.load()
            queue.enqueue(job)
            self._production_repo.save(queue)
            order.status = OrderStatus.PRODUCING
            self._order_repo.save(order)
```

---

## 메서드 명세

| 메서드 | 파라미터 | 반환 | 예외 |
|--------|----------|------|------|
| `approve` | `order_id` | `None` | `ValueError` — 존재하지 않는 주문 |

### 생성자 변경

```python
# Phase 4
OrderController(sample_repo, order_repo)

# Phase 5 (production_repo 추가, 기본값 None으로 하위 호환 유지)
OrderController(sample_repo, order_repo, production_repo=None)
```

Phase 4 테스트는 `production_repo` 없이 생성하므로 기본값 `None`으로 기존 테스트가 깨지지 않는다.

---

## Step 3 — 확인 명령어

```bash
# Phase 5 승인 테스트만 실행
python -m pytest tests/test_order_controller.py::TestApproveWithSufficientStock tests/test_order_controller.py::TestApproveWithInsufficientStock -v

# 전체 테스트 실행 (Phase 1~4 포함, 기존 테스트 깨지지 않아야 함)
python -m pytest
```

모든 테스트 통과 후 `docs/PLAN.md`의 Phase 5 체크리스트를 `[x]`로 표시한다.
