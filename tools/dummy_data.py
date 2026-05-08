import math
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

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
