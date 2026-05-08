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
