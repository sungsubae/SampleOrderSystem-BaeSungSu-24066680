import json
import pytest
from tools.monitor import print_monitor


class TestMonitor:
    def _setup_data(self, tmp_path):
        samples = [
            {"sample_id": "S001", "name": "AlGaN", "avg_production_time": 2.0, "yield_rate": 0.9, "stock": 15},
            {"sample_id": "S002", "name": "GaAs",  "avg_production_time": 3.0, "yield_rate": 0.8, "stock": 0},
        ]
        orders = [
            {"order_id": "O001", "sample_id": "S001", "customer": "연구소A", "quantity": 10, "status": "RESERVED"},
            {"order_id": "O002", "sample_id": "S002", "customer": "팹리스B", "quantity": 5,  "status": "CONFIRMED"},
            {"order_id": "O003", "sample_id": "S001", "customer": "대학C",   "quantity": 20, "status": "PRODUCING"},
        ]
        queue = [
            {"order_id": "O003", "sample_id": "S001", "actual_production": 25, "total_time": 50.0, "produced_so_far": 0},
        ]
        (tmp_path / "samples.json").write_text(json.dumps(samples), encoding="utf-8")
        (tmp_path / "orders.json").write_text(json.dumps(orders),   encoding="utf-8")
        (tmp_path / "production_queue.json").write_text(json.dumps(queue), encoding="utf-8")

    def test_shows_sample_section(self, capsys, tmp_path):
        self._setup_data(tmp_path)
        print_monitor(data_dir=tmp_path)
        out = capsys.readouterr().out
        assert "시료 현황" in out
        assert "AlGaN" in out
        assert "GaAs" in out

    def test_shows_order_status_summary(self, capsys, tmp_path):
        self._setup_data(tmp_path)
        print_monitor(data_dir=tmp_path)
        out = capsys.readouterr().out
        assert "주문 현황" in out
        assert "RESERVED" in out
        assert "CONFIRMED" in out
        assert "PRODUCING" in out

    def test_shows_order_details_in_list(self, capsys, tmp_path):
        self._setup_data(tmp_path)
        print_monitor(data_dir=tmp_path)
        out = capsys.readouterr().out
        assert "연구소A" in out
        assert "팹리스B" in out
        assert "O001" in out or "O001"[:8] in out

    def test_shows_production_queue(self, capsys, tmp_path):
        self._setup_data(tmp_path)
        print_monitor(data_dir=tmp_path)
        out = capsys.readouterr().out
        assert "생산 큐" in out
        assert "S001" in out

    def test_shows_empty_message_when_no_data(self, capsys, tmp_path):
        print_monitor(data_dir=tmp_path)
        out = capsys.readouterr().out
        assert "없습니다" in out

    def test_sample_count_in_header(self, capsys, tmp_path):
        self._setup_data(tmp_path)
        print_monitor(data_dir=tmp_path)
        out = capsys.readouterr().out
        assert "2개" in out
