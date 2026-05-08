# Phase 7 세부 설계 — ReleaseController

> TDD 순서: 테스트 작성(Red) → 구현(Green) → 전체 테스트 통과 확인 → 리팩토링 → 전체 테스트 통과 확인

---

## 대상 파일

| 구분 | 파일 |
|------|------|
| 구현 | `controllers/release_controller.py` |
| 테스트 | `tests/test_release_controller.py` |

---

## 역할 및 의존성

```
ReleaseController
    │
    ├── OrderRepository  (CONFIRMED 주문 조회, RELEASE 전환 저장)
    │
    └── 메서드
         list_confirmed() -> list[Order]
         release(order_id)
```

---

## 처리 흐름

### `release`

```
1. order_id로 주문 조회
2. 주문이 없으면 ValueError
3. 주문 상태가 CONFIRMED가 아니면 ValueError
4. 주문 상태를 CONFIRMED → RELEASE 전환 후 저장
```

---

## Step 1 — 테스트 작성 (Red)

### `tests/test_release_controller.py`

```python
import pytest
from controllers.release_controller import ReleaseController
from controllers.order_controller import OrderController
from repositories.order_repository import OrderRepository
from repositories.sample_repository import SampleRepository
from repositories.production_repository import ProductionRepository
from models.sample import Sample
from models.order import OrderStatus


@pytest.fixture
def repos(tmp_path):
    sample_repo     = SampleRepository(tmp_path / "samples.json")
    order_repo      = OrderRepository(tmp_path / "orders.json")
    production_repo = ProductionRepository(tmp_path / "production_queue.json")
    sample_repo.save(Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=0.9, stock=100))
    return sample_repo, order_repo, production_repo


@pytest.fixture
def release_ctrl(repos):
    _, order_repo, _ = repos
    return ReleaseController(order_repo=order_repo)


@pytest.fixture
def confirmed_order(repos):
    """재고 충분으로 CONFIRMED 상태인 주문"""
    sample_repo, order_repo, production_repo = repos
    order_ctrl = OrderController(
        sample_repo=sample_repo,
        order_repo=order_repo,
        production_repo=production_repo,
    )
    order = order_ctrl.reserve(sample_id="S001", customer="홍길동", quantity=5)
    order_ctrl.approve(order.order_id)  # stock=100 >= quantity=5 → CONFIRMED
    return order, ReleaseController(order_repo=order_repo)


# ── list_confirmed ────────────────────────────────────────────
class TestListConfirmed:
    def test_returns_empty_when_no_confirmed_orders(self, release_ctrl):
        assert release_ctrl.list_confirmed() == []

    def test_returns_only_confirmed_orders(self, confirmed_order):
        order, ctrl = confirmed_order
        result = ctrl.list_confirmed()
        assert len(result) == 1
        assert result[0].order_id == order.order_id
        assert result[0].status == OrderStatus.CONFIRMED


# ── release ───────────────────────────────────────────────────
class TestRelease:
    def test_release_changes_status_to_release(self, confirmed_order):
        order, ctrl = confirmed_order
        ctrl.release(order.order_id)
        assert len(ctrl.list_confirmed()) == 0

    def test_released_order_status_is_release(self, confirmed_order, repos):
        _, order_repo, _ = repos
        order, ctrl = confirmed_order
        ctrl.release(order.order_id)
        updated = order_repo.find_by_id(order.order_id)
        assert updated.status == OrderStatus.RELEASE

    def test_release_nonexistent_order_raises(self, release_ctrl):
        with pytest.raises(ValueError):
            release_ctrl.release("NONEXISTENT")

    def test_release_non_confirmed_order_raises(self, repos):
        sample_repo, order_repo, production_repo = repos
        order_ctrl = OrderController(
            sample_repo=sample_repo,
            order_repo=order_repo,
            production_repo=production_repo,
        )
        order = order_ctrl.reserve(sample_id="S001", customer="홍길동", quantity=5)
        # RESERVED 상태 → release 불가
        ctrl = ReleaseController(order_repo=order_repo)
        with pytest.raises(ValueError):
            ctrl.release(order.order_id)
```

---

## Step 2 — 구현 (Green)

### `controllers/release_controller.py`

```python
from models.order import Order, OrderStatus
from repositories.order_repository import OrderRepository


class ReleaseController:
    def __init__(self, order_repo: OrderRepository):
        self._order_repo = order_repo

    def list_confirmed(self) -> list[Order]:
        return self._order_repo.find_by_status(OrderStatus.CONFIRMED)

    def release(self, order_id: str) -> None:
        order = self._order_repo.find_by_id(order_id)
        if order is None:
            raise ValueError(f"존재하지 않는 주문입니다: {order_id}")
        if order.status != OrderStatus.CONFIRMED:
            raise ValueError(f"CONFIRMED 상태의 주문만 출고할 수 있습니다: {order.status.value}")
        order.status = OrderStatus.RELEASE
        self._order_repo.save(order)
```

---

## 메서드 명세

| 메서드 | 파라미터 | 반환 | 예외 |
|--------|----------|------|------|
| `list_confirmed` | — | `list[Order]` | — |
| `release` | `order_id` | `None` | `ValueError` — 존재하지 않는 주문 또는 CONFIRMED 아닌 상태 |

---

## Step 3 — 확인 명령어

```bash
# Phase 7 테스트만 실행
python -m pytest tests/test_release_controller.py -v

# 전체 테스트 실행 (Phase 1~6 포함)
python -m pytest
```

모든 테스트 통과 후 `docs/PLAN.md`의 Phase 7 체크리스트를 `[x]`로 표시한다.
