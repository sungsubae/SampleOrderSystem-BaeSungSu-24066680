# Phase 4 세부 설계 — OrderController (접수·거절)

> TDD 순서: 테스트 작성(Red) → 구현(Green) → 전체 테스트 통과 확인 → 리팩토링 → 전체 테스트 통과 확인

---

## 대상 파일

| 구분 | 파일 |
|------|------|
| 구현 | `controllers/order_controller.py` |
| 테스트 | `tests/test_order_controller.py` |

> Phase 5에서 `approve` 로직이 추가되므로, 이번 Phase는 접수·거절만 구현한다.

---

## 역할 및 의존성

```
OrderController
    │
    ├── SampleRepository   (시료 존재 여부 확인)
    ├── OrderRepository    (주문 CRUD, 상태별 조회)
    │
    └── 메서드 (Phase 4)
         reserve(sample_id, customer, quantity) -> Order
         list_reserved() -> list[Order]
         reject(order_id)
```

- `reserve` 시 `order_id`는 `uuid4`로 자동 생성한다.
- `reject` 시 존재하지 않는 `order_id`면 `ValueError`를 발생시킨다.

---

## Step 1 — 테스트 작성 (Red)

### `tests/test_order_controller.py`

```python
import pytest
from controllers.order_controller import OrderController
from repositories.order_repository import OrderRepository
from repositories.sample_repository import SampleRepository
from models.order import OrderStatus
from models.sample import Sample


@pytest.fixture
def repos(tmp_path):
    sample_repo = SampleRepository(tmp_path / "samples.json")
    order_repo  = OrderRepository(tmp_path / "orders.json")
    return sample_repo, order_repo


@pytest.fixture
def ctrl(repos):
    sample_repo, order_repo = repos
    return OrderController(sample_repo=sample_repo, order_repo=order_repo)


@pytest.fixture
def ctrl_with_sample(repos):
    sample_repo, order_repo = repos
    sample_repo.save(Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=0.9))
    return OrderController(sample_repo=sample_repo, order_repo=order_repo)


# ── reserve ──────────────────────────────────────────────────
class TestReserve:
    def test_reserve_returns_order_with_reserved_status(self, ctrl_with_sample):
        order = ctrl_with_sample.reserve(sample_id="S001", customer="홍길동", quantity=10)
        assert order.status == OrderStatus.RESERVED

    def test_reserve_stores_correct_fields(self, ctrl_with_sample):
        order = ctrl_with_sample.reserve(sample_id="S001", customer="홍길동", quantity=10)
        assert order.sample_id == "S001"
        assert order.customer == "홍길동"
        assert order.quantity == 10

    def test_reserve_generates_unique_order_id(self, ctrl_with_sample):
        order1 = ctrl_with_sample.reserve(sample_id="S001", customer="홍길동", quantity=10)
        order2 = ctrl_with_sample.reserve(sample_id="S001", customer="이순신", quantity=5)
        assert order1.order_id != order2.order_id

    def test_reserve_with_unregistered_sample_raises(self, ctrl):
        with pytest.raises(ValueError):
            ctrl.reserve(sample_id="NONE", customer="홍길동", quantity=10)


# ── list_reserved ─────────────────────────────────────────────
class TestListReserved:
    def test_returns_only_reserved_orders(self, ctrl_with_sample):
        ctrl_with_sample.reserve(sample_id="S001", customer="홍길동", quantity=10)
        ctrl_with_sample.reserve(sample_id="S001", customer="이순신", quantity=5)
        result = ctrl_with_sample.list_reserved()
        assert len(result) == 2
        assert all(o.status == OrderStatus.RESERVED for o in result)

    def test_returns_empty_when_no_reserved_orders(self, ctrl):
        assert ctrl.list_reserved() == []


# ── reject ────────────────────────────────────────────────────
class TestReject:
    def test_reject_changes_status_to_rejected(self, ctrl_with_sample):
        order = ctrl_with_sample.reserve(sample_id="S001", customer="홍길동", quantity=10)
        ctrl_with_sample.reject(order.order_id)
        result = ctrl_with_sample.list_reserved()
        assert len(result) == 0

    def test_rejected_order_not_in_list_reserved(self, ctrl_with_sample):
        order = ctrl_with_sample.reserve(sample_id="S001", customer="홍길동", quantity=10)
        ctrl_with_sample.reject(order.order_id)
        assert all(o.order_id != order.order_id for o in ctrl_with_sample.list_reserved())

    def test_reject_nonexistent_order_raises(self, ctrl):
        with pytest.raises(ValueError):
            ctrl.reject("NONEXISTENT")
```

---

## Step 2 — 구현 (Green)

### `controllers/order_controller.py`

```python
import uuid
from models.order import Order, OrderStatus
from repositories.order_repository import OrderRepository
from repositories.sample_repository import SampleRepository


class OrderController:
    def __init__(self, sample_repo: SampleRepository, order_repo: OrderRepository):
        self._sample_repo = sample_repo
        self._order_repo  = order_repo

    def reserve(self, sample_id: str, customer: str, quantity: int) -> Order:
        if self._sample_repo.find_by_id(sample_id) is None:
            raise ValueError(f"등록되지 않은 시료입니다: {sample_id}")
        order = Order(
            order_id=str(uuid.uuid4()),
            sample_id=sample_id,
            customer=customer,
            quantity=quantity,
        )
        self._order_repo.save(order)
        return order

    def list_reserved(self) -> list[Order]:
        return self._order_repo.find_by_status(OrderStatus.RESERVED)

    def reject(self, order_id: str) -> None:
        order = self._order_repo.find_by_id(order_id)
        if order is None:
            raise ValueError(f"존재하지 않는 주문입니다: {order_id}")
        order.status = OrderStatus.REJECTED
        self._order_repo.save(order)
```

---

## 메서드 명세

| 메서드 | 파라미터 | 반환 | 예외 |
|--------|----------|------|------|
| `reserve` | `sample_id`, `customer`, `quantity` | `Order` | `ValueError` — 미등록 시료 |
| `list_reserved` | — | `list[Order]` | — |
| `reject` | `order_id` | `None` | `ValueError` — 존재하지 않는 주문 |

### order_id 생성 규칙

- `uuid.uuid4()` 문자열로 자동 생성
- 호출마다 고유값 보장

---

## Step 3 — 확인 명령어

```bash
# Phase 4 테스트만 실행
python -m pytest tests/test_order_controller.py -v

# 전체 테스트 실행 (Phase 1·2·3 포함)
python -m pytest
```

모든 테스트 통과 후 `docs/PLAN.md`의 Phase 4 체크리스트를 `[x]`로 표시한다.
