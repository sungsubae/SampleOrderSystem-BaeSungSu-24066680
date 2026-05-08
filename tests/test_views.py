import pytest
from controllers.sample_controller import SampleController
from controllers.order_controller import OrderController
from repositories.sample_repository import SampleRepository
from repositories.order_repository import OrderRepository
from repositories.production_repository import ProductionRepository
from models.sample import Sample
from views.sample_view import SampleView
from views.order_view import OrderView


@pytest.fixture
def sample_ctrl(tmp_path):
    repo = SampleRepository(tmp_path / "samples.json")
    return SampleController(repo)


@pytest.fixture
def order_ctrl(tmp_path):
    sample_repo     = SampleRepository(tmp_path / "samples.json")
    order_repo      = OrderRepository(tmp_path / "orders.json")
    production_repo = ProductionRepository(tmp_path / "production_queue.json")
    sample_repo.save(Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=0.9, stock=10))
    return OrderController(sample_repo=sample_repo, order_repo=order_repo, production_repo=production_repo)


# ── SampleView ────────────────────────────────────────────────
class TestSampleView:
    def test_register_success_prints_confirmation(self, monkeypatch, capsys, sample_ctrl):
        inputs = iter(["1", "S001", "AlGaN", "2.0", "0.9", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        SampleView(sample_ctrl).menu()
        out = capsys.readouterr().out
        assert "AlGaN" in out
        assert "✔" in out

    def test_register_duplicate_id_prints_error(self, monkeypatch, capsys, sample_ctrl):
        sample_ctrl.register(sample_id="S001", name="AlGaN", avg_time=2.0, yield_rate=0.9)
        inputs = iter(["1", "S001", "AlGaN", "2.0", "0.9", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        SampleView(sample_ctrl).menu()
        out = capsys.readouterr().out
        assert "✖" in out

    def test_list_all_shows_registered_samples(self, monkeypatch, capsys, sample_ctrl):
        sample_ctrl.register(sample_id="S001", name="AlGaN", avg_time=2.0, yield_rate=0.9)
        inputs = iter(["2", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        SampleView(sample_ctrl).menu()
        out = capsys.readouterr().out
        assert "S001" in out
        assert "AlGaN" in out

    def test_search_returns_matching(self, monkeypatch, capsys, sample_ctrl):
        sample_ctrl.register(sample_id="S001", name="AlGaN",  avg_time=2.0, yield_rate=0.9)
        sample_ctrl.register(sample_id="S002", name="GaAs",   avg_time=3.0, yield_rate=0.8)
        inputs = iter(["3", "Al", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        SampleView(sample_ctrl).menu()
        out = capsys.readouterr().out
        assert "AlGaN" in out
        assert "GaAs" not in out

    def test_invalid_yield_rate_shows_error(self, monkeypatch, capsys, sample_ctrl):
        inputs = iter(["1", "S001", "AlGaN", "2.0", "abc", "0.9", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        SampleView(sample_ctrl).menu()
        out = capsys.readouterr().out
        assert "숫자를 입력해주세요" in out


# ── OrderView ─────────────────────────────────────────────────
class TestOrderView:
    def test_reserve_success_prints_confirmation(self, monkeypatch, capsys, order_ctrl):
        inputs = iter(["1", "S001", "홍길동", "5", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        OrderView(order_ctrl).menu()
        out = capsys.readouterr().out
        assert "✔" in out

    def test_reserve_unknown_sample_prints_error(self, monkeypatch, capsys, order_ctrl):
        inputs = iter(["1", "NONE", "홍길동", "5", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        OrderView(order_ctrl).menu()
        out = capsys.readouterr().out
        assert "✖" in out

    def test_approve_order_prints_confirmation(self, monkeypatch, capsys, order_ctrl):
        order_ctrl.reserve(sample_id="S001", customer="홍길동", quantity=5)
        inputs = iter(["2", "1", "a", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        OrderView(order_ctrl).menu()
        out = capsys.readouterr().out
        assert "✔" in out

    def test_no_reserved_orders_shows_message(self, monkeypatch, capsys, order_ctrl):
        inputs = iter(["2", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        OrderView(order_ctrl).menu()
        out = capsys.readouterr().out
        assert "접수된 주문이 없습니다" in out
