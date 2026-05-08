import pytest
from models.order import Order, OrderStatus
from models.sample import Sample
from models.production_line import ProductionJob, ProductionQueue
from repositories.json_repository import load, save
from repositories.sample_repository import SampleRepository
from repositories.order_repository import OrderRepository
from repositories.production_repository import ProductionRepository


# ── JsonRepository ───────────────────────────────────────────
class TestJsonRepository:
    def test_save_and_load_roundtrip(self, tmp_path):
        filepath = tmp_path / "test.json"
        data = {"key": "value", "number": 42}
        save(filepath, data)
        result = load(filepath)
        assert result == data

    def test_load_returns_empty_dict_when_file_not_exists(self, tmp_path):
        filepath = tmp_path / "nonexistent.json"
        result = load(filepath)
        assert result == {}

    def test_save_creates_file_with_indent(self, tmp_path):
        filepath = tmp_path / "test.json"
        save(filepath, {"a": 1})
        content = filepath.read_text(encoding="utf-8")
        assert "\n" in content


# ── SampleRepository ─────────────────────────────────────────
class TestSampleRepository:
    def test_save_and_find_all(self, tmp_path):
        repo = SampleRepository(tmp_path / "samples.json")
        sample = Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=0.9)
        repo.save(sample)
        result = repo.find_all()
        assert len(result) == 1
        assert result[0].sample_id == "S001"
        assert result[0].name == "AlGaN"

    def test_find_by_id(self, tmp_path):
        repo = SampleRepository(tmp_path / "samples.json")
        repo.save(Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=0.9))
        result = repo.find_by_id("S001")
        assert result is not None
        assert result.sample_id == "S001"

    def test_find_by_id_returns_none_when_not_found(self, tmp_path):
        repo = SampleRepository(tmp_path / "samples.json")
        assert repo.find_by_id("NONE") is None

    def test_find_all_returns_empty_when_no_file(self, tmp_path):
        repo = SampleRepository(tmp_path / "samples.json")
        assert repo.find_all() == []

    def test_save_multiple_and_find_all(self, tmp_path):
        repo = SampleRepository(tmp_path / "samples.json")
        repo.save(Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=0.9))
        repo.save(Sample(sample_id="S002", name="GaAs",  avg_production_time=3.0, yield_rate=0.8))
        result = repo.find_all()
        assert len(result) == 2

    def test_save_overwrites_existing(self, tmp_path):
        repo = SampleRepository(tmp_path / "samples.json")
        repo.save(Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=0.9))
        repo.save(Sample(sample_id="S001", name="AlGaN-Updated", avg_production_time=2.0, yield_rate=0.9))
        result = repo.find_all()
        assert len(result) == 1
        assert result[0].name == "AlGaN-Updated"

    def test_data_persists_across_instances(self, tmp_path):
        filepath = tmp_path / "samples.json"
        repo1 = SampleRepository(filepath)
        repo1.save(Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=0.9))
        repo2 = SampleRepository(filepath)
        result = repo2.find_all()
        assert len(result) == 1
        assert result[0].sample_id == "S001"


# ── OrderRepository ──────────────────────────────────────────
class TestOrderRepository:
    def _make_order(self, order_id: str, status: OrderStatus = OrderStatus.RESERVED) -> Order:
        order = Order(order_id=order_id, sample_id="S001", customer="홍길동", quantity=10)
        order.status = status
        return order

    def test_save_and_find_all(self, tmp_path):
        repo = OrderRepository(tmp_path / "orders.json")
        repo.save(self._make_order("O001"))
        result = repo.find_all()
        assert len(result) == 1
        assert result[0].order_id == "O001"

    def test_find_by_id(self, tmp_path):
        repo = OrderRepository(tmp_path / "orders.json")
        repo.save(self._make_order("O001"))
        result = repo.find_by_id("O001")
        assert result is not None
        assert result.order_id == "O001"

    def test_find_by_id_returns_none_when_not_found(self, tmp_path):
        repo = OrderRepository(tmp_path / "orders.json")
        assert repo.find_by_id("NONE") is None

    def test_find_all_returns_empty_when_no_file(self, tmp_path):
        repo = OrderRepository(tmp_path / "orders.json")
        assert repo.find_all() == []

    def test_find_by_status_reserved(self, tmp_path):
        repo = OrderRepository(tmp_path / "orders.json")
        repo.save(self._make_order("O001", OrderStatus.RESERVED))
        repo.save(self._make_order("O002", OrderStatus.CONFIRMED))
        repo.save(self._make_order("O003", OrderStatus.RESERVED))
        result = repo.find_by_status(OrderStatus.RESERVED)
        assert len(result) == 2
        assert all(o.status == OrderStatus.RESERVED for o in result)

    def test_find_by_status_returns_empty_when_none_match(self, tmp_path):
        repo = OrderRepository(tmp_path / "orders.json")
        repo.save(self._make_order("O001", OrderStatus.RESERVED))
        result = repo.find_by_status(OrderStatus.RELEASE)
        assert result == []

    def test_status_persisted_correctly(self, tmp_path):
        repo = OrderRepository(tmp_path / "orders.json")
        repo.save(self._make_order("O001", OrderStatus.PRODUCING))
        result = repo.find_by_id("O001")
        assert result.status == OrderStatus.PRODUCING

    def test_data_persists_across_instances(self, tmp_path):
        filepath = tmp_path / "orders.json"
        repo1 = OrderRepository(filepath)
        repo1.save(self._make_order("O001"))
        repo2 = OrderRepository(filepath)
        assert len(repo2.find_all()) == 1


# ── ProductionRepository ─────────────────────────────────────
class TestProductionRepository:
    def _make_job(self, order_id: str) -> ProductionJob:
        return ProductionJob(order_id=order_id, sample_id="S001", actual_production=5, total_time=10.0)

    def test_save_and_load_queue(self, tmp_path):
        repo = ProductionRepository(tmp_path / "production_queue.json")
        queue = ProductionQueue()
        queue.enqueue(self._make_job("O001"))
        repo.save(queue)
        result = repo.load()
        assert result.size() == 1
        assert result.peek().order_id == "O001"

    def test_fifo_order_preserved_after_load(self, tmp_path):
        repo = ProductionRepository(tmp_path / "production_queue.json")
        queue = ProductionQueue()
        queue.enqueue(self._make_job("O001"))
        queue.enqueue(self._make_job("O002"))
        queue.enqueue(self._make_job("O003"))
        repo.save(queue)
        result = repo.load()
        assert result.dequeue().order_id == "O001"
        assert result.dequeue().order_id == "O002"
        assert result.dequeue().order_id == "O003"

    def test_load_returns_empty_queue_when_no_file(self, tmp_path):
        repo = ProductionRepository(tmp_path / "production_queue.json")
        result = repo.load()
        assert result.is_empty()

    def test_data_persists_across_instances(self, tmp_path):
        filepath = tmp_path / "production_queue.json"
        repo1 = ProductionRepository(filepath)
        queue = ProductionQueue()
        queue.enqueue(self._make_job("O001"))
        repo1.save(queue)
        repo2 = ProductionRepository(filepath)
        result = repo2.load()
        assert result.size() == 1
