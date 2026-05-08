# Phase 1 세부 설계 — 도메인 모델

> TDD 순서: 테스트 작성(Red) → 구현(Green) → 전체 테스트 통과 확인

---

## 대상 파일

| 구분 | 파일 |
|------|------|
| 구현 | `models/__init__.py` |
| 구현 | `models/order.py` |
| 구현 | `models/sample.py` |
| 구현 | `models/production_line.py` |
| 테스트 | `tests/__init__.py` |
| 테스트 | `tests/test_models.py` |

---

## Step 1 — 테스트 작성 (Red)

### `tests/test_models.py`

```python
import pytest
from models.order import Order, OrderStatus
from models.sample import Sample
from models.production_line import ProductionJob, ProductionQueue


# ── OrderStatus ──────────────────────────────────────────────
class TestOrderStatus:
    def test_all_statuses_exist(self):
        statuses = {s.value for s in OrderStatus}
        assert statuses == {"RESERVED", "REJECTED", "PRODUCING", "CONFIRMED", "RELEASE"}


# ── Order ────────────────────────────────────────────────────
class TestOrder:
    def test_default_status_is_reserved(self):
        order = Order(order_id="O001", sample_id="S001", customer="홍길동", quantity=10)
        assert order.status == OrderStatus.RESERVED

    def test_fields_stored_correctly(self):
        order = Order(order_id="O001", sample_id="S001", customer="홍길동", quantity=10)
        assert order.order_id == "O001"
        assert order.sample_id == "S001"
        assert order.customer == "홍길동"
        assert order.quantity == 10

    def test_status_can_be_changed(self):
        order = Order(order_id="O001", sample_id="S001", customer="홍길동", quantity=10)
        order.status = OrderStatus.CONFIRMED
        assert order.status == OrderStatus.CONFIRMED


# ── Sample ───────────────────────────────────────────────────
class TestSample:
    def test_fields_stored_correctly(self):
        sample = Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=0.9)
        assert sample.sample_id == "S001"
        assert sample.name == "AlGaN"
        assert sample.avg_production_time == 2.0
        assert sample.yield_rate == 0.9

    def test_default_stock_is_zero(self):
        sample = Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=0.9)
        assert sample.stock == 0

    def test_yield_rate_zero_raises(self):
        with pytest.raises(ValueError):
            Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=0)

    def test_yield_rate_negative_raises(self):
        with pytest.raises(ValueError):
            Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=-0.1)

    def test_yield_rate_greater_than_one_raises(self):
        with pytest.raises(ValueError):
            Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=1.1)


# ── ProductionJob ────────────────────────────────────────────
class TestProductionJob:
    def test_fields_stored_correctly(self):
        job = ProductionJob(order_id="O001", sample_id="S001", actual_production=12, total_time=24.0)
        assert job.order_id == "O001"
        assert job.actual_production == 12
        assert job.total_time == 24.0

    def test_default_produced_so_far_is_zero(self):
        job = ProductionJob(order_id="O001", sample_id="S001", actual_production=12, total_time=24.0)
        assert job.produced_so_far == 0


# ── ProductionQueue ──────────────────────────────────────────
class TestProductionQueue:
    def _make_job(self, order_id: str) -> ProductionJob:
        return ProductionJob(order_id=order_id, sample_id="S001", actual_production=5, total_time=10.0)

    def test_enqueue_and_dequeue_fifo(self):
        q = ProductionQueue()
        q.enqueue(self._make_job("O001"))
        q.enqueue(self._make_job("O002"))
        q.enqueue(self._make_job("O003"))
        assert q.dequeue().order_id == "O001"
        assert q.dequeue().order_id == "O002"
        assert q.dequeue().order_id == "O003"

    def test_peek_does_not_remove(self):
        q = ProductionQueue()
        q.enqueue(self._make_job("O001"))
        assert q.peek().order_id == "O001"
        assert q.size() == 1

    def test_empty_queue_dequeue_raises(self):
        q = ProductionQueue()
        with pytest.raises(IndexError):
            q.dequeue()

    def test_empty_queue_peek_returns_none(self):
        q = ProductionQueue()
        assert q.peek() is None

    def test_size(self):
        q = ProductionQueue()
        assert q.size() == 0
        q.enqueue(self._make_job("O001"))
        assert q.size() == 1

    def test_is_empty(self):
        q = ProductionQueue()
        assert q.is_empty() is True
        q.enqueue(self._make_job("O001"))
        assert q.is_empty() is False

    def test_to_list_preserves_order(self):
        q = ProductionQueue()
        q.enqueue(self._make_job("O001"))
        q.enqueue(self._make_job("O002"))
        ids = [job.order_id for job in q.to_list()]
        assert ids == ["O001", "O002"]
```

---

## Step 2 — 구현 (Green)

### `models/order.py`

```python
from dataclasses import dataclass
from enum import Enum


class OrderStatus(Enum):
    RESERVED  = "RESERVED"
    REJECTED  = "REJECTED"
    PRODUCING = "PRODUCING"
    CONFIRMED = "CONFIRMED"
    RELEASE   = "RELEASE"


@dataclass
class Order:
    order_id: str
    sample_id: str
    customer: str
    quantity: int
    status: OrderStatus = OrderStatus.RESERVED
```

### `models/sample.py`

```python
from dataclasses import dataclass


@dataclass
class Sample:
    sample_id: str
    name: str
    avg_production_time: float
    yield_rate: float
    stock: int = 0

    def __post_init__(self):
        if not (0 < self.yield_rate <= 1):
            raise ValueError(f"yield_rate는 0 초과 1 이하여야 합니다: {self.yield_rate}")
```

### `models/production_line.py`

```python
from collections import deque
from dataclasses import dataclass


@dataclass
class ProductionJob:
    order_id: str
    sample_id: str
    actual_production: int
    total_time: float
    produced_so_far: int = 0


class ProductionQueue:
    def __init__(self):
        self._queue: deque[ProductionJob] = deque()

    def enqueue(self, job: ProductionJob) -> None:
        self._queue.append(job)

    def dequeue(self) -> ProductionJob:
        if self.is_empty():
            raise IndexError("생산 큐가 비어 있습니다.")
        return self._queue.popleft()

    def peek(self) -> ProductionJob | None:
        return self._queue[0] if self._queue else None

    def size(self) -> int:
        return len(self._queue)

    def is_empty(self) -> bool:
        return len(self._queue) == 0

    def to_list(self) -> list[ProductionJob]:
        return list(self._queue)
```

### `models/__init__.py`

```python
from .order import Order, OrderStatus
from .sample import Sample
from .production_line import ProductionJob, ProductionQueue
```

---

## 클래스 다이어그램

```
┌─────────────────────────────┐
│         OrderStatus         │
│─────────────────────────────│
│ RESERVED                    │
│ REJECTED                    │
│ PRODUCING                   │
│ CONFIRMED                   │
│ RELEASE                     │
└─────────────────────────────┘

┌─────────────────────────────┐
│            Order            │
│─────────────────────────────│
│ order_id  : str             │
│ sample_id : str             │
│ customer  : str             │
│ quantity  : int             │
│ status    : OrderStatus     │  (기본값: RESERVED)
└─────────────────────────────┘

┌─────────────────────────────┐
│           Sample            │
│─────────────────────────────│
│ sample_id           : str   │
│ name                : str   │
│ avg_production_time : float │
│ yield_rate          : float │  (0 < yield_rate ≤ 1)
│ stock               : int   │  (기본값: 0)
└─────────────────────────────┘

┌─────────────────────────────┐
│        ProductionJob        │
│─────────────────────────────│
│ order_id          : str     │
│ sample_id         : str     │
│ actual_production : int     │
│ total_time        : float   │
│ produced_so_far   : int     │  (기본값: 0)
└─────────────────────────────┘

┌─────────────────────────────┐
│       ProductionQueue       │
│─────────────────────────────│
│ _queue : deque[ProductionJob]│
│─────────────────────────────│
│ enqueue(job)                │
│ dequeue() -> ProductionJob  │
│ peek() -> ProductionJob|None│
│ size() -> int               │
│ is_empty() -> bool          │
│ to_list() -> list           │
└─────────────────────────────┘
```

---

## 필드 명세

### Order

| 필드 | 타입 | 기본값 | 제약 |
|------|------|--------|------|
| `order_id` | `str` | 필수 | 시스템 내 고유 |
| `sample_id` | `str` | 필수 | 등록된 Sample 참조 |
| `customer` | `str` | 필수 | — |
| `quantity` | `int` | 필수 | > 0 |
| `status` | `OrderStatus` | `RESERVED` | enum 값만 허용 |

### Sample

| 필드 | 타입 | 기본값 | 제약 |
|------|------|--------|------|
| `sample_id` | `str` | 필수 | 시스템 내 고유 |
| `name` | `str` | 필수 | — |
| `avg_production_time` | `float` | 필수 | > 0 |
| `yield_rate` | `float` | 필수 | 0 < yield_rate ≤ 1 |
| `stock` | `int` | `0` | ≥ 0 |

### ProductionJob

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `order_id` | `str` | 필수 | 연결된 주문 ID |
| `sample_id` | `str` | 필수 | 생산할 시료 ID |
| `actual_production` | `int` | 필수 | `ceil(부족분 / (yield_rate × 0.9))` |
| `total_time` | `float` | 필수 | `avg_production_time × actual_production` |
| `produced_so_far` | `int` | `0` | 현재까지 생산 완료 수량 |

---

## Step 3 — 확인 명령어

```bash
# Phase 1 테스트만 실행
python -m pytest tests/test_models.py -v

# 전체 테스트 실행
python -m pytest
```

모든 테스트 통과 후 `docs/PLAN.md`의 Phase 1 체크리스트를 `[x]`로 표시한다.
