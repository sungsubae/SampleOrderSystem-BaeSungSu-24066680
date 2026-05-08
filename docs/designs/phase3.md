# Phase 3 세부 설계 — SampleController

> TDD 순서: 테스트 작성(Red) → 구현(Green) → 전체 테스트 통과 확인 → 리팩토링 → 전체 테스트 통과 확인

---

## 대상 파일

| 구분 | 파일 |
|------|------|
| 구현 | `controllers/__init__.py` |
| 구현 | `controllers/sample_controller.py` |
| 테스트 | `tests/test_sample_controller.py` |

---

## 역할 및 의존성

```
SampleController
    │
    ├── SampleRepository  (data/samples.json 읽기/쓰기)
    │
    └── 메서드
         register(sample_id, name, avg_time, yield_rate)
         list_all() -> list[Sample]
         search(keyword) -> list[Sample]
```

- Controller는 비즈니스 로직만 담당하고 데이터 접근은 Repository에 위임한다.
- 테스트에서는 `tmp_path` fixture로 격리된 Repository 인스턴스를 사용한다.

---

## Step 1 — 테스트 작성 (Red)

### `tests/test_sample_controller.py`

```python
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
        ctrl.register(sample_id="S001", name="AlGaN", avg_time=2.0, yield_rate=0.9)
        ctrl.register(sample_id="S002", name="GaAs",  avg_time=3.0, yield_rate=0.8)
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
```

---

## Step 2 — 구현 (Green)

### `controllers/sample_controller.py`

```python
from models.sample import Sample
from repositories.sample_repository import SampleRepository


class SampleController:
    def __init__(self, repository: SampleRepository):
        self._repo = repository

    def register(self, sample_id: str, name: str, avg_time: float, yield_rate: float) -> Sample:
        if self._repo.find_by_id(sample_id) is not None:
            raise ValueError(f"이미 등록된 시료 ID입니다: {sample_id}")
        sample = Sample(
            sample_id=sample_id,
            name=name,
            avg_production_time=avg_time,
            yield_rate=yield_rate,
        )
        self._repo.save(sample)
        return sample

    def list_all(self) -> list[Sample]:
        return self._repo.find_all()

    def search(self, keyword: str) -> list[Sample]:
        keyword_lower = keyword.lower()
        return [s for s in self._repo.find_all() if keyword_lower in s.name.lower()]
```

---

## 메서드 명세

| 메서드 | 파라미터 | 반환 | 예외 |
|--------|----------|------|------|
| `register` | `sample_id`, `name`, `avg_time`, `yield_rate` | `Sample` | `ValueError` — 중복 ID |
| `list_all` | — | `list[Sample]` | — |
| `search` | `keyword: str` | `list[Sample]` | — |

### 검색 규칙

- 시료 `name` 필드에 `keyword`가 포함되면 반환
- 대소문자 구분 없음 (양쪽 모두 `.lower()` 적용)

---

## Step 3 — 확인 명령어

```bash
# Phase 3 테스트만 실행
python -m pytest tests/test_sample_controller.py -v

# 전체 테스트 실행 (Phase 1·2 포함)
python -m pytest
```

모든 테스트 통과 후 `docs/PLAN.md`의 Phase 3 체크리스트를 `[x]`로 표시한다.
