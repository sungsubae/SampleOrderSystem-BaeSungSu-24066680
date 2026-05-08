import json
import pytest
from pathlib import Path
from tools.dummy_data import generate_dummy_data


class TestDummyData:
    def test_creates_samples_json(self, tmp_path):
        generate_dummy_data(data_dir=tmp_path)
        assert (tmp_path / "samples.json").exists()

    def test_creates_orders_json(self, tmp_path):
        generate_dummy_data(data_dir=tmp_path)
        assert (tmp_path / "orders.json").exists()

    def test_creates_production_queue_json(self, tmp_path):
        generate_dummy_data(data_dir=tmp_path)
        assert (tmp_path / "production_queue.json").exists()

    def test_samples_count(self, tmp_path):
        generate_dummy_data(data_dir=tmp_path)
        samples = json.loads((tmp_path / "samples.json").read_text(encoding="utf-8"))
        assert len(samples) >= 3

    def test_orders_count(self, tmp_path):
        generate_dummy_data(data_dir=tmp_path)
        orders = json.loads((tmp_path / "orders.json").read_text(encoding="utf-8"))
        assert len(orders) >= 10

    def test_orders_have_various_statuses(self, tmp_path):
        generate_dummy_data(data_dir=tmp_path)
        orders = json.loads((tmp_path / "orders.json").read_text(encoding="utf-8"))
        statuses = {o["status"] for o in orders}
        assert statuses >= {"RESERVED", "PRODUCING", "CONFIRMED", "RELEASE"}

    def test_producing_orders_have_queue_jobs(self, tmp_path):
        generate_dummy_data(data_dir=tmp_path)
        orders = json.loads((tmp_path / "orders.json").read_text(encoding="utf-8"))
        queue  = json.loads((tmp_path / "production_queue.json").read_text(encoding="utf-8"))
        producing_ids = {o["order_id"] for o in orders if o["status"] == "PRODUCING"}
        queue_ids     = {j["order_id"] for j in queue}
        assert producing_ids == queue_ids

    def test_overwrites_existing_data(self, tmp_path):
        generate_dummy_data(data_dir=tmp_path)
        generate_dummy_data(data_dir=tmp_path)
        orders = json.loads((tmp_path / "orders.json").read_text(encoding="utf-8"))
        assert len(orders) >= 10
