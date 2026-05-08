"""
E2E 테스트 스크립트

tools/dummy_data.py 로 더미 데이터를 생성하고,
main.py(build_main_view)를 통해 전체 흐름을 실행한 뒤,
tools/monitor.py(print_monitor)로 최종 상태를 검증합니다.

검증 시나리오:
  1. 더미 데이터 모니터 확인
  2. 재고 충분 → 승인(CONFIRMED) → 출고(RELEASE)
  3. 재고 부족 → 승인(PRODUCING) → 생산 완료 → 출고(RELEASE)
  4. 주문 거절(REJECTED) → 모니터링 미노출
"""

import pytest
from models.order import OrderStatus
from models.sample import Sample
from repositories.order_repository import OrderRepository
from repositories.production_repository import ProductionRepository
from repositories.sample_repository import SampleRepository
from tools.dummy_data import generate_dummy_data
from tools.monitor import print_monitor
from main import build_main_view


# ── 공통 헬퍼 ────────────────────────────────────────────────────
def _setup_sample(tmp_path, sample_id: str, stock: int) -> None:
    SampleRepository(tmp_path / "samples.json").save(
        Sample(sample_id=sample_id, name="TestSample",
               avg_production_time=1.0, yield_rate=0.9, stock=stock)
    )


def _run(tmp_path, monkeypatch, inputs: list):
    it = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda _: next(it))
    build_main_view(data_dir=tmp_path).run()


# ── 시나리오 1: 더미 데이터 기반 모니터 확인 ────────────────────────
class TestE2EDummyData:
    def test_all_statuses_present_after_dummy_data(self, tmp_path, capsys):
        """더미 데이터 생성 후 monitor에서 4가지 주문 상태가 모두 출력되는지 확인"""
        generate_dummy_data(data_dir=tmp_path)
        print_monitor(data_dir=tmp_path)
        out = capsys.readouterr().out
        for status in ["RESERVED", "PRODUCING", "CONFIRMED", "RELEASE"]:
            assert status in out, f"{status} 상태가 monitor 출력에 없음"

    def test_all_samples_present_after_dummy_data(self, tmp_path, capsys):
        """더미 데이터 생성 후 monitor에서 4개 시료가 모두 출력되는지 확인"""
        generate_dummy_data(data_dir=tmp_path)
        print_monitor(data_dir=tmp_path)
        out = capsys.readouterr().out
        for name in ["AlGaN", "GaAs", "InGaAs", "SiC"]:
            assert name in out, f"시료 '{name}'이 monitor 출력에 없음"

    def test_dummy_data_monitoring_via_main_app(self, tmp_path, monkeypatch, capsys):
        """더미 데이터 로드 후 main 앱에서 모니터링 화면 진입 확인"""
        generate_dummy_data(data_dir=tmp_path)
        _run(tmp_path, monkeypatch, ["3", "0"])  # 모니터링 → 종료
        out = capsys.readouterr().out
        assert "모니터링" in out
        assert "RESERVED" in out

    def test_rejected_orders_excluded_from_main_monitoring(self, tmp_path, monkeypatch, capsys):
        """더미 데이터(REJECTED 포함) 로드 후 main 모니터링에 REJECTED 미출력 확인"""
        generate_dummy_data(data_dir=tmp_path)
        _run(tmp_path, monkeypatch, ["3", "0"])
        out = capsys.readouterr().out
        # 모니터링 섹션에 REJECTED 상태 행이 없어야 함
        monitoring_part = out.split("모니터링")[-1] if "모니터링" in out else out
        assert "▶ REJECTED" not in monitoring_part


# ── 시나리오 2: 재고 충분 → CONFIRMED → 출고(RELEASE) ───────────────
class TestE2ESufficientStockFlow:
    def test_full_flow_confirmed_to_release(self, tmp_path, monkeypatch, capsys):
        """재고 충분 → 주문 접수 → 승인(CONFIRMED) → 출고(RELEASE) 전체 흐름"""
        _setup_sample(tmp_path, "E001", stock=20)

        _run(tmp_path, monkeypatch, [
            "2",             # 주문 관리
            "1",             # 주문 접수
            "E001", "홍길동", "10",   # 시료 ID / 고객명 / 수량
            "2",             # 주문 승인/거절
            "1", "a",        # 첫 번째 주문 승인
            "0",             # 주문 관리 종료
            "4",             # 출고 처리
            "1",             # 첫 번째 출고
            "0",             # 종료
        ])

        order_repo  = OrderRepository(tmp_path / "orders.json")
        sample_repo = SampleRepository(tmp_path / "samples.json")

        released = order_repo.find_by_status(OrderStatus.RELEASE)
        assert len(released) == 1
        assert released[0].customer == "홍길동"
        assert released[0].quantity == 10

        # approve 시 재고 차감 (20 - 10 = 10), release 시 추가 차감 없음
        assert sample_repo.find_by_id("E001").stock == 10

    def test_stock_prevents_duplicate_approval(self, tmp_path, monkeypatch, capsys):
        """재고 차감 후 두 번째 주문이 재고 부족으로 PRODUCING 전환되는지 확인"""
        _setup_sample(tmp_path, "E001", stock=10)

        _run(tmp_path, monkeypatch, [
            "2",
            "1", "E001", "고객A", "8",   # 주문A (8개)
            "1", "E001", "고객B", "8",   # 주문B (8개)
            "2",
            "1", "a",   # 주문A 승인 → CONFIRMED, stock 10→2
            "2",
            "1", "a",   # 주문B 승인 → stock 2 < 8 → PRODUCING
            "0",
            "0",
        ])

        order_repo = OrderRepository(tmp_path / "orders.json")
        confirmed  = order_repo.find_by_status(OrderStatus.CONFIRMED)
        producing  = order_repo.find_by_status(OrderStatus.PRODUCING)
        assert len(confirmed) == 1 and confirmed[0].customer == "고객A"
        assert len(producing) == 1 and producing[0].customer == "고객B"

    def test_monitor_shows_release_after_full_flow(self, tmp_path, monkeypatch, capsys):
        """출고 완료 후 monitor에서 RELEASE 상태 확인"""
        _setup_sample(tmp_path, "E001", stock=20)

        _run(tmp_path, monkeypatch, [
            "2", "1", "E001", "홍길동", "10",
            "2", "1", "a", "0",
            "4", "1",
            "0",
        ])

        print_monitor(data_dir=tmp_path)
        out = capsys.readouterr().out
        assert "RELEASE" in out
        assert "홍길동" in out


# ── 시나리오 3: 재고 부족 → PRODUCING → 생산 완료 → RELEASE ─────────
class TestE2EProducingFlow:
    def test_insufficient_stock_creates_production_job(self, tmp_path, monkeypatch, capsys):
        """재고 부족 → 승인(PRODUCING) + 생산 큐 등록 확인"""
        _setup_sample(tmp_path, "E001", stock=0)

        _run(tmp_path, monkeypatch, [
            "2",
            "1", "E001", "이순신", "10",
            "2", "1", "a",
            "0", "0",
        ])

        order_repo      = OrderRepository(tmp_path / "orders.json")
        production_repo = ProductionRepository(tmp_path / "production_queue.json")

        producing = order_repo.find_by_status(OrderStatus.PRODUCING)
        assert len(producing) == 1
        assert producing[0].customer == "이순신"

        queue = production_repo.load()
        assert queue.size() == 1
        assert queue.peek().order_id == producing[0].order_id

    def test_full_flow_producing_to_release(self, tmp_path, monkeypatch, capsys):
        """재고 부족 → PRODUCING → 생산 완료 → CONFIRMED → 출고(RELEASE) 전체 흐름"""
        from controllers.order_controller import OrderController

        # 컨트롤러로 PRODUCING 상태까지 설정
        sample_repo     = SampleRepository(tmp_path / "samples.json")
        order_repo      = OrderRepository(tmp_path / "orders.json")
        production_repo = ProductionRepository(tmp_path / "production_queue.json")
        sample_repo.save(Sample(sample_id="E001", name="TestSample",
                                avg_production_time=1.0, yield_rate=0.9, stock=0))
        order_ctrl = OrderController(sample_repo, order_repo, production_repo)
        order = order_ctrl.reserve("E001", "장보고", 5)
        order_ctrl.approve(order.order_id)  # stock=0 < 5 → PRODUCING

        assert order_repo.find_by_id(order.order_id).status == OrderStatus.PRODUCING

        # main 앱으로 생산 완료 처리 → 출고
        _run(tmp_path, monkeypatch, [
            "5",               # 생산 라인 → 생산 완료 처리
            order.order_id,    # 완료할 주문 ID (전체 UUID)
            "4",               # 출고 처리
            "1",               # 첫 번째 출고
            "0",               # 종료
        ])

        released = order_repo.find_by_status(OrderStatus.RELEASE)
        assert len(released) == 1
        assert released[0].customer == "장보고"

        # monitor 최종 확인
        print_monitor(data_dir=tmp_path)
        out = capsys.readouterr().out
        assert "RELEASE" in out
        assert "장보고" in out


# ── 시나리오 4: 주문 거절(REJECTED) → 모니터링 미노출 ───────────────
class TestE2ERejectFlow:
    def test_rejected_order_not_in_monitoring(self, tmp_path, monkeypatch, capsys):
        """주문 거절 후 모니터링 화면에 해당 주문 미노출 확인"""
        _setup_sample(tmp_path, "E001", stock=10)

        _run(tmp_path, monkeypatch, [
            "2",
            "1", "E001", "강감찬", "5",
            "2", "1", "r",   # 거절
            "0",
            "3",             # 모니터링
            "0",
        ])

        order_repo = OrderRepository(tmp_path / "orders.json")
        rejected = order_repo.find_by_status(OrderStatus.REJECTED)
        assert len(rejected) == 1
        assert rejected[0].customer == "강감찬"

        # 모니터링 출력에 강감찬 미노출
        out = capsys.readouterr().out
        monitoring_section = out.split("모니터링")[-1] if "모니터링" in out else out
        assert "강감찬" not in monitoring_section

    def test_monitor_tool_shows_rejected(self, tmp_path, monkeypatch, capsys):
        """관리자 monitor 도구는 REJECTED도 포함해서 출력하는지 확인"""
        _setup_sample(tmp_path, "E001", stock=10)

        _run(tmp_path, monkeypatch, [
            "2", "1", "E001", "강감찬", "5",
            "2", "1", "r",
            "0", "0",
        ])

        print_monitor(data_dir=tmp_path)
        out = capsys.readouterr().out
        assert "REJECTED" in out
        assert "강감찬" in out
