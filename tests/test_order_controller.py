import math
import pytest
from controllers.order_controller import OrderController
from repositories.order_repository import OrderRepository
from repositories.sample_repository import SampleRepository
from repositories.production_repository import ProductionRepository
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


@pytest.fixture
def ctrl_full(tmp_path):
    sample_repo     = SampleRepository(tmp_path / "samples.json")
    order_repo      = OrderRepository(tmp_path / "orders.json")
    production_repo = ProductionRepository(tmp_path / "production_queue.json")
    sample_repo.save(Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=0.9))
    return OrderController(
        sample_repo=sample_repo,
        order_repo=order_repo,
        production_repo=production_repo,
    )


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


# ── approve (재고 충분) ───────────────────────────────────────
class TestApproveWithSufficientStock:
    def test_status_becomes_confirmed(self, ctrl_full, tmp_path):
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

    def test_approve_sufficient_stock_decrements_stock(self, ctrl_full, tmp_path):
        sample_repo = SampleRepository(tmp_path / "samples.json")
        sample = sample_repo.find_by_id("S001")
        sample.stock = 10
        sample_repo.save(sample)
        order = ctrl_full.reserve(sample_id="S001", customer="홍길동", quantity=5)
        ctrl_full.approve(order.order_id)
        updated_sample = sample_repo.find_by_id("S001")
        assert updated_sample.stock == 5  # 10 - 5

    def test_approve_second_order_sees_reduced_stock(self, ctrl_full, tmp_path):
        """첫 번째 승인 후 재고가 차감되어 두 번째 주문이 PRODUCING으로 전환되는지 확인."""
        sample_repo = SampleRepository(tmp_path / "samples.json")
        sample = sample_repo.find_by_id("S001")
        sample.stock = 10
        sample_repo.save(sample)
        order_a = ctrl_full.reserve(sample_id="S001", customer="홍길동", quantity=8)
        order_b = ctrl_full.reserve(sample_id="S001", customer="이순신", quantity=8)
        ctrl_full.approve(order_a.order_id)  # stock 10 → 2
        ctrl_full.approve(order_b.order_id)  # stock 2 < 8 → PRODUCING
        assert ctrl_full._order_repo.find_by_id(order_a.order_id).status == OrderStatus.CONFIRMED
        assert ctrl_full._order_repo.find_by_id(order_b.order_id).status == OrderStatus.PRODUCING


# ── approve (재고 부족) ───────────────────────────────────────
class TestApproveWithInsufficientStock:
    def test_status_becomes_producing(self, ctrl_full):
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
