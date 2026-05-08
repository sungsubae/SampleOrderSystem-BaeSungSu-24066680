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
    sample_repo, order_repo, _ = repos
    return ReleaseController(order_repo=order_repo, sample_repo=sample_repo)


@pytest.fixture
def confirmed_order(repos):
    sample_repo, order_repo, production_repo = repos
    order_ctrl = OrderController(
        sample_repo=sample_repo,
        order_repo=order_repo,
        production_repo=production_repo,
    )
    order = order_ctrl.reserve(sample_id="S001", customer="홍길동", quantity=5)
    order_ctrl.approve(order.order_id)
    return order, ReleaseController(order_repo=order_repo, sample_repo=sample_repo)


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
        ctrl = ReleaseController(order_repo=order_repo, sample_repo=sample_repo)
        with pytest.raises(ValueError):
            ctrl.release(order.order_id)

    def test_release_decrements_stock(self, confirmed_order, repos):
        sample_repo, _, _ = repos
        order, ctrl = confirmed_order
        stock_before = sample_repo.find_by_id("S001").stock  # 100
        ctrl.release(order.order_id)
        stock_after = sample_repo.find_by_id("S001").stock
        assert stock_after == stock_before - order.quantity  # 100 - 5 = 95
