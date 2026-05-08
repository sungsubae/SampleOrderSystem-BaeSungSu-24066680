# Phase 6 세부 설계 — ProductionController

> TDD 순서: 테스트 작성(Red) → 구현(Green) → 전체 테스트 통과 확인 -> 리팩토링 -> 전체 테스트 통과 확인

---

## 대상 파일

| 구분 | 파일 |
|------|------|
| 구현 | `controllers/production_controller.py` |
| 테스트 | `tests/test_production_controller.py` |

---

## 역할 및 의존성

```
ProductionController
    │
    ├── ProductionRepository  (생산 큐 로드·저장)
    ├── OrderRepository       (주문 상태 CONFIRMED 전환)
    ├── SampleRepository      (시료 재고 증가)
    │
    └── 메서드
         get_current_job() -> ProductionJob | None
         list_queue()      -> list[ProductionJob]
         complete_job(order_id)
```

### `get_current_job` vs `list_queue` 구분

| 메서드 | 설명 |
|--------|------|
| `get_current_job()` | 큐 맨 앞 Job (현재 생산 중) — `peek()`으로 조회, 큐에서 제거하지 않음 |
| `list_queue()` | 큐 전체 목록 — `to_list()`로 조회, 순서 유지 |

---

## `complete_job` 처리 흐름

```
1. 큐에서 Job을 dequeue
2. 해당 시료의 재고 += job.actual_production
3. 해당 주문 상태를 PRODUCING → CONFIRMED 전환
4. 변경사항 저장 (SampleRepository, OrderRepository, ProductionRepository)
```

- 큐가 비어 있을 때 `complete_job` 호출 시 `IndexError` 발생
- `order_id`에 해당하는 Job이 큐에 없을 때 `ValueError` 발생

---

## Step 1 — 테스트 작성 (Red)

### `tests/test_production_controller.py`

```python
import pytest
from controllers.production_controller import ProductionController
from controllers.order_controller import OrderController
from repositories.production_repository import ProductionRepository
from repositories.order_repository import OrderRepository
from repositories.sample_repository import SampleRepository
from models.sample import Sample
from models.order import OrderStatus


@pytest.fixture
def repos(tmp_path):
    sample_repo     = SampleRepository(tmp_path / "samples.json")
    order_repo      = OrderRepository(tmp_path / "orders.json")
    production_repo = ProductionRepository(tmp_path / "production_queue.json")
    sample_repo.save(Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=0.9))
    return sample_repo, order_repo, production_repo


@pytest.fixture
def ctrl(repos):
    sample_repo, order_repo, production_repo = repos
    return ProductionController(
        production_repo=production_repo,
        order_repo=order_repo,
        sample_repo=sample_repo,
    )


@pytest.fixture
def ctrl_with_producing_order(repos):
    """재고 부족으로 PRODUCING 상태인 주문이 큐에 있는 상태"""
    sample_repo, order_repo, production_repo = repos
    order_ctrl = OrderController(
        sample_repo=sample_repo,
        order_repo=order_repo,
        production_repo=production_repo,
    )
    order = order_ctrl.reserve(sample_id="S001", customer="홍길동", quantity=10)
    order_ctrl.approve(order.order_id)  # 재고 0 → PRODUCING, 큐 등록
    prod_ctrl = ProductionController(
        production_repo=production_repo,
        order_repo=order_repo,
        sample_repo=sample_repo,
    )
    return prod_ctrl, order


# ── get_current_job ───────────────────────────────────────────
class TestGetCurrentJob:
    def test_returns_none_when_queue_empty(self, ctrl):
        assert ctrl.get_current_job() is None

    def test_returns_first_job_without_removing(self, ctrl_with_producing_order):
        prod_ctrl, order = ctrl_with_producing_order
        job = prod_ctrl.get_current_job()
        assert job is not None
        assert job.order_id == order.order_id
        assert prod_ctrl.get_current_job() is not None  # 여전히 존재


# ── list_queue ────────────────────────────────────────────────
class TestListQueue:
    def test_returns_empty_when_no_jobs(self, ctrl):
        assert ctrl.list_queue() == []

    def test_returns_all_jobs_in_fifo_order(self, repos):
        sample_repo, order_repo, production_repo = repos
        order_ctrl = OrderController(
            sample_repo=sample_repo,
            order_repo=order_repo,
            production_repo=production_repo,
        )
        order1 = order_ctrl.reserve(sample_id="S001", customer="홍길동", quantity=10)
        order2 = order_ctrl.reserve(sample_id="S001", customer="이순신", quantity=5)
        order_ctrl.approve(order1.order_id)
        order_ctrl.approve(order2.order_id)
        prod_ctrl = ProductionController(
            production_repo=production_repo,
            order_repo=order_repo,
            sample_repo=sample_repo,
        )
        queue = prod_ctrl.list_queue()
        assert len(queue) == 2
        assert queue[0].order_id == order1.order_id
        assert queue[1].order_id == order2.order_id


# ── complete_job ──────────────────────────────────────────────
class TestCompleteJob:
    def test_order_status_becomes_confirmed(self, ctrl_with_producing_order):
        prod_ctrl, order = ctrl_with_producing_order
        prod_ctrl.complete_job(order.order_id)
        updated_order = prod_ctrl._order_repo.find_by_id(order.order_id)
        assert updated_order.status == OrderStatus.CONFIRMED

    def test_stock_increases_by_actual_production(self, ctrl_with_producing_order, repos):
        sample_repo, _, _ = repos
        prod_ctrl, order = ctrl_with_producing_order
        job = prod_ctrl.get_current_job()
        expected_stock = job.actual_production
        prod_ctrl.complete_job(order.order_id)
        updated_sample = sample_repo.find_by_id("S001")
        assert updated_sample.stock == expected_stock

    def test_job_removed_from_queue_after_complete(self, ctrl_with_producing_order):
        prod_ctrl, order = ctrl_with_producing_order
        prod_ctrl.complete_job(order.order_id)
        assert prod_ctrl.get_current_job() is None

    def test_complete_job_on_empty_queue_raises(self, ctrl):
        with pytest.raises((IndexError, ValueError)):
            ctrl.complete_job("NONEXISTENT")
```

---

## Step 2 — 구현 (Green)

### `controllers/production_controller.py`

```python
from models.order import OrderStatus
from repositories.order_repository import OrderRepository
from repositories.production_repository import ProductionRepository
from repositories.sample_repository import SampleRepository


class ProductionController:
    def __init__(
        self,
        production_repo: ProductionRepository,
        order_repo: OrderRepository,
        sample_repo: SampleRepository,
    ):
        self._production_repo = production_repo
        self._order_repo      = order_repo
        self._sample_repo     = sample_repo

    def get_current_job(self):
        return self._production_repo.load().peek()

    def list_queue(self) -> list:
        return self._production_repo.load().to_list()

    def complete_job(self, order_id: str) -> None:
        queue = self._production_repo.load()
        job = queue.dequeue()                       # 비어 있으면 IndexError

        # 재고 증가
        sample = self._sample_repo.find_by_id(job.sample_id)
        sample.stock += job.actual_production
        self._sample_repo.save(sample)

        # 주문 상태 CONFIRMED 전환
        order = self._order_repo.find_by_id(job.order_id)
        order.status = OrderStatus.CONFIRMED
        self._order_repo.save(order)

        # 큐 저장
        self._production_repo.save(queue)
```

---

## 메서드 명세

| 메서드 | 파라미터 | 반환 | 예외 |
|--------|----------|------|------|
| `get_current_job` | — | `ProductionJob \| None` | — |
| `list_queue` | — | `list[ProductionJob]` | — |
| `complete_job` | `order_id` | `None` | `IndexError` — 빈 큐 |

---

## Step 3 — 확인 명령어

```bash
# Phase 6 테스트만 실행
python -m pytest tests/test_production_controller.py -v

# 전체 테스트 실행 (Phase 1~5 포함)
python -m pytest
```

모든 테스트 통과 후 `docs/PLAN.md`의 Phase 6 체크리스트를 `[x]`로 표시한다.
