import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from views.common import header, section, divider

DATA_DIR = Path("data")


def _load(filepath: Path) -> list:
    if not filepath.exists():
        return []
    return json.loads(filepath.read_text(encoding="utf-8"))


def print_monitor(data_dir: Path = DATA_DIR) -> None:
    data_dir = Path(data_dir)
    samples = _load(data_dir / "samples.json")
    orders  = _load(data_dir / "orders.json")
    queue   = _load(data_dir / "production_queue.json")

    header("S-Semi 관리자 데이터 모니터")

    # ── 시료 현황 ──────────────────────────────────────────
    section(f"시료 현황 ({len(samples)}개)")
    if not samples:
        print("  등록된 시료가 없습니다.")
    else:
        print(f"  {'ID':<12} {'이름':<14} {'생산시간':>8}  {'수율':>6}  {'재고':>5}")
        divider()
        for s in samples:
            print(f"  {s['sample_id']:<12} {s['name']:<14} "
                  f"{s['avg_production_time']:>6.1f}h  "
                  f"{s['yield_rate']*100:>5.1f}%  {s['stock']:>5}")

    # ── 주문 현황 ──────────────────────────────────────────
    section(f"주문 현황 ({len(orders)}개)")
    if not orders:
        print("  주문이 없습니다.")
    else:
        status_order = ["RESERVED", "PRODUCING", "CONFIRMED", "RELEASE", "REJECTED"]
        counts = {s: sum(1 for o in orders if o["status"] == s) for s in status_order}
        print(f"  {'상태':<14} {'건수':>5}")
        divider()
        for status in status_order:
            if counts[status] > 0:
                print(f"  {status:<14} {counts[status]:>5}")

    # ── 생산 큐 현황 ───────────────────────────────────────
    section(f"생산 큐 현황 ({len(queue)}개)")
    if not queue:
        print("  대기 중인 작업이 없습니다.")
    else:
        print(f"  {'순서':<5} {'주문ID':<14} {'시료ID':<10} {'생산수량':>8}  {'예상시간':>8}")
        divider()
        for i, job in enumerate(queue, 1):
            print(f"  [{i}]   {job['order_id'][:8]:<14} {job['sample_id']:<10} "
                  f"{job['actual_production']:>8}  {job['total_time']:>7.1f}h")


if __name__ == "__main__":
    print_monitor()
