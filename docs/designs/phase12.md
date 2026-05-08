# Phase 12 세부 설계 — 관리자용 데이터 모니터링 도구

> TDD 순서: 테스트 작성(Red) → 구현(Green) → 전체 테스트 통과 확인 → 리팩토링 → 전체 테스트 통과 확인

---

## 대상 파일

| 구분 | 파일 |
|------|------|
| 구현 | `tools/monitor.py` |
| 테스트 | `tests/test_monitor.py` |

---

## 역할

`tools/monitor.py`는 앱 실행 없이 독립적으로 `data/*.json`을 직접 읽어  
현재 데이터 상태를 콘솔에 포맷 출력하는 관리자용 도구다.

```bash
python tools/monitor.py
```

---

## 화면 예시

```
╔══════════════════════════════════════════════════════════════╗
║               S-Semi 관리자 데이터 모니터                      ║
╚══════════════════════════════════════════════════════════════╝

┌─ 시료 현황 (4개) ─────────────────────────────────────────────┐
  ID          이름          생산시간    수율    재고
  ──────────────────────────────────────────────────────────
  S001        AlGaN         2.0h      90.0%     15
  S002        GaAs          3.0h      80.0%      0
  S003        InGaAs        1.5h      95.0%     30
  S004        SiC           4.0h      75.0%      5

┌─ 주문 현황 (12개) ────────────────────────────────────────────┐
  상태         건수
  ──────────────────────────────────────────────────────────
  RESERVED      2
  PRODUCING     2
  CONFIRMED     3
  RELEASE       4
  REJECTED      1

┌─ 생산 큐 현황 (2개) ──────────────────────────────────────────┐
  순서   주문ID       시료ID    생산수량   예상시간
  ──────────────────────────────────────────────────────────
  [1]    a1b2c3d4     S001         25     50.0h
  [2]    e5f6g7h8     S003         10     15.0h
```

---

## Step 1 — 테스트 작성 (Red)

### `tests/test_monitor.py`

```python
import json
import pytest
from pathlib import Path
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
        (tmp_path / "orders.json").write_text(json.dumps(orders),  encoding="utf-8")
        (tmp_path / "production_queue.json").write_text(json.dumps(queue), encoding="utf-8")
        return tmp_path

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

    def test_shows_production_queue(self, capsys, tmp_path):
        self._setup_data(tmp_path)
        print_monitor(data_dir=tmp_path)
        out = capsys.readouterr().out
        assert "생산 큐" in out
        assert "O003" in out or "S001" in out

    def test_shows_empty_message_when_no_data(self, capsys, tmp_path):
        print_monitor(data_dir=tmp_path)
        out = capsys.readouterr().out
        assert "시료 없음" in out or "0개" in out or "등록된" in out

    def test_sample_count_in_header(self, capsys, tmp_path):
        self._setup_data(tmp_path)
        print_monitor(data_dir=tmp_path)
        out = capsys.readouterr().out
        assert "2개" in out  # 시료 2개
```

---

## Step 2 — 구현 (Green)

### `tools/monitor.py`

```python
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
```

---

## Step 3 — 확인 명령어

```bash
# 테스트 실행
python -m pytest tests/test_monitor.py -v

# 더미 데이터 생성 후 모니터링
python tools/dummy_data.py
python tools/monitor.py
```

모든 테스트 통과 후 `docs/PLAN.md`의 Phase 12 체크리스트를 `[x]`로 표시한다.
