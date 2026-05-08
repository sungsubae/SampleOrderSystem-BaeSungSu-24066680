import pytest
from controllers.sample_controller import SampleController
from repositories.sample_repository import SampleRepository


@pytest.fixture
def ctrl(tmp_path):
    repo = SampleRepository(tmp_path / "samples.json")
    return SampleController(repo)


# ── register ─────────────────────────────────────────────────
class TestRegister:
    def test_registered_sample_appears_in_list_all(self, ctrl):
        ctrl.register(sample_id="S001", name="AlGaN", avg_time=2.0, yield_rate=0.9)
        result = ctrl.list_all()
        assert len(result) == 1
        assert result[0].sample_id == "S001"

    def test_duplicate_sample_id_raises(self, ctrl):
        ctrl.register(sample_id="S001", name="AlGaN", avg_time=2.0, yield_rate=0.9)
        with pytest.raises(ValueError):
            ctrl.register(sample_id="S001", name="AlGaN-dup", avg_time=2.0, yield_rate=0.9)

    def test_register_stores_all_fields(self, ctrl):
        ctrl.register(sample_id="S001", name="AlGaN", avg_time=2.0, yield_rate=0.9)
        sample = ctrl.list_all()[0]
        assert sample.name == "AlGaN"
        assert sample.avg_production_time == 2.0
        assert sample.yield_rate == 0.9
        assert sample.stock == 0

    def test_register_multiple_samples(self, ctrl):
        ctrl.register(sample_id="S001", name="AlGaN", avg_time=2.0, yield_rate=0.9)
        ctrl.register(sample_id="S002", name="GaAs",  avg_time=3.0, yield_rate=0.8)
        assert len(ctrl.list_all()) == 2


# ── list_all ─────────────────────────────────────────────────
class TestListAll:
    def test_returns_empty_when_no_samples(self, ctrl):
        assert ctrl.list_all() == []

    def test_returns_all_registered_samples(self, ctrl):
        ctrl.register(sample_id="S001", name="AlGaN", avg_time=2.0, yield_rate=0.9)
        ctrl.register(sample_id="S002", name="GaAs",  avg_time=3.0, yield_rate=0.8)
        ids = {s.sample_id for s in ctrl.list_all()}
        assert ids == {"S001", "S002"}


# ── search ───────────────────────────────────────────────────
class TestSearch:
    def test_search_returns_matching_samples(self, ctrl):
        ctrl.register(sample_id="S001", name="AlGaN",  avg_time=2.0, yield_rate=0.9)
        ctrl.register(sample_id="S002", name="GaAs",   avg_time=3.0, yield_rate=0.8)
        ctrl.register(sample_id="S003", name="AlGaAs", avg_time=4.0, yield_rate=0.7)
        result = ctrl.search("Al")
        assert len(result) == 2
        assert all("Al" in s.name for s in result)

    def test_search_is_case_insensitive(self, ctrl):
        ctrl.register(sample_id="S001", name="AlGaN", avg_time=2.0, yield_rate=0.9)
        result = ctrl.search("algan")
        assert len(result) == 1

    def test_search_returns_empty_when_no_match(self, ctrl):
        ctrl.register(sample_id="S001", name="AlGaN", avg_time=2.0, yield_rate=0.9)
        assert ctrl.search("ZZZ") == []

    def test_search_returns_empty_when_no_samples(self, ctrl):
        assert ctrl.search("Al") == []
