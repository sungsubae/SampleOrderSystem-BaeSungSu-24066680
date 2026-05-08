# Phase 11 세부 설계 — 더미 데이터 생성 도구

> TDD 순서: 테스트 작성(Red) → 구현(Green) → 전체 테스트 통과 확인 → 리팩토링 → 전체 테스트 통과 확인

---

## 대상 파일

| 구분 | 파일 |
|------|------|
| 구현 | `tools/__init__.py` |
| 구현 | `tools/dummy_data.py` |
| 테스트 | `tests/test_dummy_data.py` |

---

## 역할

`tools/dummy_data.py`는 앱 실행 없이 독립적으로 동작하는 스크립트로,  
테스트 목적의 더미 데이터를 생성하여 `data/*.json`에 직접 저장한다.

```bash
python tools/dummy_data.py
```

---

## 생성할 더미 데이터

### 시료 (4개)

| sample_id | name   | avg_production_time | yield_rate | stock |
|-----------|--------|---------------------|------------|-------|
| S001      | AlGaN  | 2.0                 | 0.9        | 15    |
| S002      | GaAs   | 3.0                 | 0.8        | 0     |
| S003      | InGaAs | 1.5                 | 0.95       | 30    |
| S004      | SiC    | 4.0                 | 0.75       | 5     |

### 주문 (12개) — 다양한 상태 포함

| order_id (자동) | sample_id | customer | quantity | status    |
|-----------------|-----------|----------|----------|-----------|
| 자동 생성        | S001      | 연구소A  | 10       | RESERVED  |
| 자동 생성        | S002      | 팹리스B  | 5        | RESERVED  |
| 자동 생성        | S001      | 대학C    | 20       | PRODUCING |
| 자동 생성        | S003      | 연구소A  | 8        | PRODUCING |
| 자동 생성        | S002      | 팹리스B  | 3        | CONFIRMED |
| 자동 생성        | S004      | 대학C    | 12       | CONFIRMED |
| 자동 생성        | S001      | 연구소A  | 7        | CONFIRMED |
| 자동 생성        | S003      | 팹리스B  | 15       | RELEASE   |
| 자동 생성        | S002      | 대학C    | 4        | RELEASE   |
| 자동 생성        | S004      | 연구소A  | 9        | RELEASE   |
| 자동 생성        | S001      | 팹리스B  | 6        | RELEASE   |
| 자동 생성        | S003      | 대학C    | 11       | REJECTED  |

### 생산 큐 (PRODUCING 주문에 대응하는 Job 2개)

| order_id      | sample_id | actual_production | total_time | produced_so_far |
|---------------|-----------|-------------------|------------|-----------------|
| (S001 PRODUCING) | S001   | 계산값            | 계산값     | 0               |
| (S003 PRODUCING) | S003   | 계산값            | 계산값     | 0               |

> `actual_production = ceil(quantity / (yield_rate * 0.9))`

---

## Step 1 — 테스트 작성 (Red)

### `tests/test_dummy_data.py`

```python
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
        assert len(orders) >= 10  # 중복 없이 덮어쓰기
```

---

## Step 2 — 구현 (Green)

### `tools/dummy_data.py`

```python
import math
import uuid
from pathlib import Path
from repositories.json_repository import save


SAMPLES = [
    {"sample_id": "S001", "name": "AlGaN",  "avg_production_time": 2.0, "yield_rate": 0.90, "stock": 15},
    {"sample_id": "S002", "name": "GaAs",   "avg_production_time": 3.0, "yield_rate": 0.80, "stock":  0},
    {"sample_id": "S003", "name": "InGaAs", "avg_production_time": 1.5, "yield_rate": 0.95, "stock": 30},
    {"sample_id": "S004", "name": "SiC",    "avg_production_time": 4.0, "yield_rate": 0.75, "stock":  5},
]

_SAMPLE_MAP = {s["sample_id"]: s for s in SAMPLES}

ORDER_TEMPLATES = [
    ("S001", "연구소A",  10, "RESERVED"),
    ("S002", "팹리스B",   5, "RESERVED"),
    ("S001", "대학C",    20, "PRODUCING"),
    ("S003", "연구소A",   8, "PRODUCING"),
    ("S002", "팹리스B",   3, "CONFIRMED"),
    ("S004", "대학C",    12, "CONFIRMED"),
    ("S001", "연구소A",   7, "CONFIRMED"),
    ("S003", "팹리스B",  15, "RELEASE"),
    ("S002", "대학C",     4, "RELEASE"),
    ("S004", "연구소A",   9, "RELEASE"),
    ("S001", "팹리스B",   6, "RELEASE"),
    ("S003", "대학C",    11, "REJECTED"),
]


def generate_dummy_data(data_dir: Path = Path("data")) -> None:
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    orders, queue = [], []
    for sample_id, customer, quantity, status in ORDER_TEMPLATES:
        order_id = str(uuid.uuid4())
        orders.append({
            "order_id": order_id,
            "sample_id": sample_id,
            "customer": customer,
            "quantity": quantity,
            "status": status,
        })
        if status == "PRODUCING":
            s = _SAMPLE_MAP[sample_id]
            actual = math.ceil(quantity / (s["yield_rate"] * 0.9))
            queue.append({
                "order_id": order_id,
                "sample_id": sample_id,
                "actual_production": actual,
                "total_time": s["avg_production_time"] * actual,
                "produced_so_far": 0,
            })

    save(data_dir / "samples.json", SAMPLES)
    save(data_dir / "orders.json", orders)
    save(data_dir / "production_queue.json", queue)
    print(f"✔ 더미 데이터 생성 완료: {data_dir}/")
    print(f"  시료 {len(SAMPLES)}개 · 주문 {len(orders)}개 · 생산 큐 {len(queue)}개")


if __name__ == "__main__":
    generate_dummy_data()
```

---

## Step 3 — 확인 명령어

```bash
# 테스트 실행
python -m pytest tests/test_dummy_data.py -v

# 실제 데이터 생성
python tools/dummy_data.py

# 생성 결과 확인
python -c "import json; print(json.load(open('data/samples.json')))"
```

모든 테스트 통과 후 `docs/PLAN.md`의 Phase 11 체크리스트를 `[x]`로 표시한다.
