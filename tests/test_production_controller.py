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
    sample_repo, order_repo, production_repo = repos
    order_ctrl = OrderController(
        sample_repo=sample_repo,
        order_repo=order_repo,
        production_repo=production_repo,
    )
    order = order_ctrl.reserve(sample_id="S001", customer="홍길동", quantity=10)
    order_ctrl.approve(order.order_id)
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
        assert prod_ctrl.get_current_job() is not None


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
