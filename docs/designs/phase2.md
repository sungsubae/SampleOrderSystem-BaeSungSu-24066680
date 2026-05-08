# Phase 2 세부 설계 — Repository (영속성 레이어)

> TDD 순서: 테스트 작성(Red) → 구현(Green) → 전체 테스트 통과 확인

---

## 대상 파일

| 구분 | 파일 |
|------|------|
| 구현 | `repositories/__init__.py` |
| 구현 | `repositories/json_repository.py` |
| 구현 | `repositories/sample_repository.py` |
| 구현 | `repositories/order_repository.py` |
| 구현 | `repositories/production_repository.py` |
| 구현 | `data/` (디렉터리, `.gitkeep` 포함) |
| 테스트 | `tests/test_repositories.py` |

---

## 아키텍처

```
json_repository.py          # load / save 공통 유틸
        ▲
        │ 사용
┌───────┴──────────────────────────────────┐
│  SampleRepository     data/samples.json  │
│  OrderRepository      data/orders.json   │
│  ProductionRepository data/production_queue.json │
└──────────────────────────────────────────┘
```

- 각 Repository는 `json_repository`의 `load` / `save`를 호출해 `data/*.json`을 관리한다.
- 변경(추가·수정·삭제) 발생 즉시 저장한다.
- 테스트에서는 `tmp_path` fixture를 사용해 실제 `data/` 디렉터리를 건드리지 않는다.

---

## Step 1 — 테스트 작성 (Red)

### `tests/test_repositories.py`

```python
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
        assert "\n" in content  # indent=2 적용 시 줄바꿈 포함


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
        sample = Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=0.9)
        repo.save(sample)
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
```

---

## Step 2 — 구현 (Green)

### `repositories/json_repository.py`

```python
import json
from pathlib import Path


def load(filepath) -> dict:
    path = Path(filepath)
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(filepath, data: dict) -> None:
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
```

### `repositories/sample_repository.py`

- `find_all() -> list[Sample]` : 전체 시료 목록 반환
- `find_by_id(sample_id) -> Sample | None` : ID로 단일 조회
- `save(sample)` : 추가 또는 덮어쓰기 후 즉시 저장

**직렬화 규칙 (`Sample` ↔ dict)**

```python
# Sample → dict
{"sample_id": s.sample_id, "name": s.name,
 "avg_production_time": s.avg_production_time,
 "yield_rate": s.yield_rate, "stock": s.stock}

# dict → Sample
Sample(sample_id=d["sample_id"], name=d["name"],
       avg_production_time=d["avg_production_time"],
       yield_rate=d["yield_rate"], stock=d["stock"])
```

### `repositories/order_repository.py`

- `find_all() -> list[Order]`
- `find_by_id(order_id) -> Order | None`
- `find_by_status(status: OrderStatus) -> list[Order]`
- `save(order)` : 추가 또는 덮어쓰기 후 즉시 저장

**직렬화 규칙 (`Order` ↔ dict)**

```python
# Order → dict
{"order_id": o.order_id, "sample_id": o.sample_id,
 "customer": o.customer, "quantity": o.quantity,
 "status": o.status.value}

# dict → Order
order = Order(order_id=d["order_id"], sample_id=d["sample_id"],
              customer=d["customer"], quantity=d["quantity"])
order.status = OrderStatus(d["status"])
```

### `repositories/production_repository.py`

- `load() -> ProductionQueue` : JSON → `ProductionQueue` 복원
- `save(queue: ProductionQueue)` : `ProductionQueue` → JSON 저장

**직렬화 규칙 (`ProductionJob` ↔ dict)**

```python
# ProductionJob → dict
{"order_id": j.order_id, "sample_id": j.sample_id,
 "actual_production": j.actual_production,
 "total_time": j.total_time, "produced_so_far": j.produced_so_far}

# dict → ProductionJob
ProductionJob(order_id=d["order_id"], sample_id=d["sample_id"],
              actual_production=d["actual_production"],
              total_time=d["total_time"],
              produced_so_far=d["produced_so_far"])
```

---

## 데이터 파일 스키마

### `data/samples.json`

```json
[
  {
    "sample_id": "S001",
    "name": "AlGaN",
    "avg_production_time": 2.0,
    "yield_rate": 0.9,
    "stock": 0
  }
]
```

### `data/orders.json`

```json
[
  {
    "order_id": "O001",
    "sample_id": "S001",
    "customer": "홍길동",
    "quantity": 10,
    "status": "RESERVED"
  }
]
```

### `data/production_queue.json`

```json
[
  {
    "order_id": "O001",
    "sample_id": "S001",
    "actual_production": 12,
    "total_time": 24.0,
    "produced_so_far": 0
  }
]
```

---

## Step 3 — 확인 명령어

```bash
# Phase 2 테스트만 실행
python -m pytest tests/test_repositories.py -v

# 전체 테스트 실행 (기존 Phase 1 포함)
python -m pytest
```

모든 테스트 통과 후 `docs/PLAN.md`의 Phase 2 체크리스트를 `[x]`로 표시한다.
