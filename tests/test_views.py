import pytest
from controllers.sample_controller import SampleController
from controllers.order_controller import OrderController
from controllers.production_controller import ProductionController
from controllers.release_controller import ReleaseController
from repositories.sample_repository import SampleRepository
from repositories.order_repository import OrderRepository
from repositories.production_repository import ProductionRepository
from models.sample import Sample
from views.sample_view import SampleView
from views.order_view import OrderView
from views.monitoring_view import MonitoringView
from views.production_view import ProductionView
from views.release_view import ReleaseView


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


# ── 공통 fixture (Phase 9) ─────────────────────────────────────
@pytest.fixture
def full_repos(tmp_path):
    sample_repo     = SampleRepository(tmp_path / "samples.json")
    order_repo      = OrderRepository(tmp_path / "orders.json")
    production_repo = ProductionRepository(tmp_path / "production_queue.json")
    sample_repo.save(Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=0.9, stock=10))
    return sample_repo, order_repo, production_repo


@pytest.fixture
def ctrls(full_repos):
    sample_repo, order_repo, production_repo = full_repos
    sample_ctrl     = SampleController(sample_repo)
    order_ctrl      = OrderController(sample_repo, order_repo, production_repo)
    production_ctrl = ProductionController(production_repo, order_repo, sample_repo)
    release_ctrl    = ReleaseController(order_repo)
    return sample_ctrl, order_ctrl, production_ctrl, release_ctrl, order_repo


# ── MonitoringView ────────────────────────────────────────────
class TestMonitoringView:
    def test_shows_order_status_counts(self, capsys, ctrls):
        sample_ctrl, order_ctrl, _, _, order_repo = ctrls
        order_ctrl.reserve(sample_id="S001", customer="홍길동", quantity=5)
        MonitoringView(sample_ctrl, order_repo).show()
        out = capsys.readouterr().out
        assert "RESERVED" in out
        assert "1건" in out

    def test_stock_tag_여유(self, capsys, ctrls):
        sample_ctrl, _, _, _, order_repo = ctrls
        MonitoringView(sample_ctrl, order_repo).show()
        out = capsys.readouterr().out
        assert "여유" in out

    def test_stock_tag_고갈(self, capsys, full_repos):
        sample_repo, order_repo, production_repo = full_repos
        sample_repo.save(Sample(sample_id="S002", name="GaAs", avg_production_time=3.0, yield_rate=0.8, stock=0))
        sample_ctrl = SampleController(sample_repo)
        MonitoringView(sample_ctrl, order_repo).show()
        out = capsys.readouterr().out
        assert "고갈" in out

    def test_stock_tag_부족(self, capsys, ctrls):
        sample_ctrl, order_ctrl, _, _, order_repo = ctrls
        order_ctrl.reserve(sample_id="S001", customer="홍길동", quantity=20)  # 재고 10 < 주문 20
        MonitoringView(sample_ctrl, order_repo).show()
        out = capsys.readouterr().out
        assert "부족" in out


# ── ProductionView ────────────────────────────────────────────
class TestProductionView:
    def test_shows_empty_message_when_queue_empty(self, monkeypatch, capsys, ctrls):
        _, _, production_ctrl, _, _ = ctrls
        monkeypatch.setattr("builtins.input", lambda _: "")
        ProductionView(production_ctrl).show()
        out = capsys.readouterr().out
        assert "현재 생산 중인 작업이 없습니다" in out

    def test_shows_current_job_info(self, monkeypatch, capsys, ctrls):
        _, order_ctrl, production_ctrl, _, _ = ctrls
        order = order_ctrl.reserve(sample_id="S001", customer="홍길동", quantity=100)  # 재고 10 < 주문 100 → PRODUCING
        order_ctrl.approve(order.order_id)
        monkeypatch.setattr("builtins.input", lambda _: "")
        ProductionView(production_ctrl).show()
        out = capsys.readouterr().out
        assert "S001" in out
        assert "생산 수량" in out

    def test_complete_job_prints_success(self, monkeypatch, capsys, ctrls):
        _, order_ctrl, production_ctrl, _, _ = ctrls
        order = order_ctrl.reserve(sample_id="S001", customer="홍길동", quantity=100)
        order_ctrl.approve(order.order_id)
        monkeypatch.setattr("builtins.input", lambda _: order.order_id)
        ProductionView(production_ctrl).show()
        out = capsys.readouterr().out
        assert "✔" in out


# ── ReleaseView ───────────────────────────────────────────────
class TestReleaseView:
    def test_shows_empty_message_when_no_confirmed(self, monkeypatch, capsys, ctrls):
        _, _, _, release_ctrl, _ = ctrls
        monkeypatch.setattr("builtins.input", lambda _: "")
        ReleaseView(release_ctrl).show()
        out = capsys.readouterr().out
        assert "출고 대기 중인 주문이 없습니다" in out

    def test_release_success_prints_confirmation(self, monkeypatch, capsys, ctrls):
        _, order_ctrl, _, release_ctrl, _ = ctrls
        order = order_ctrl.reserve(sample_id="S001", customer="홍길동", quantity=5)  # 재고 10 >= 5 → CONFIRMED
        order_ctrl.approve(order.order_id)
        inputs = iter(["1"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        ReleaseView(release_ctrl).show()
        out = capsys.readouterr().out
        assert "✔" in out
