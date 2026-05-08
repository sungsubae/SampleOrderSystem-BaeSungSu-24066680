import pytest
from models.order import Order, OrderStatus
from models.sample import Sample
from models.production_line import ProductionJob, ProductionQueue


class TestOrderStatus:
    def test_all_statuses_exist(self):
        statuses = {s.value for s in OrderStatus}
        assert statuses == {"RESERVED", "REJECTED", "PRODUCING", "CONFIRMED", "RELEASE"}


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


class TestProductionJob:
    def test_fields_stored_correctly(self):
        job = ProductionJob(order_id="O001", sample_id="S001", actual_production=12, total_time=24.0)
        assert job.order_id == "O001"
        assert job.sample_id == "S001"
        assert job.actual_production == 12
        assert job.total_time == 24.0

    def test_default_produced_so_far_is_zero(self):
        job = ProductionJob(order_id="O001", sample_id="S001", actual_production=12, total_time=24.0)
        assert job.produced_so_far == 0


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
