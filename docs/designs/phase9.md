# Phase 9 세부 설계 — View (모니터링·생산라인·출고)

> TDD 순서: 테스트 작성(Red) → 구현(Green) → 전체 테스트 통과 확인 → 리팩토링 → 전체 테스트 통과 확인

> View는 콘솔 I/O를 직접 다루므로 `monkeypatch` + `capsys`로 자동 테스트하고,  
> 수동 검증으로 시각적 출력을 보완한다.

---

## 대상 파일

| 구분 | 파일 |
|------|------|
| 구현 | `views/monitoring_view.py` |
| 구현 | `views/production_view.py` |
| 구현 | `views/release_view.py` |
| 테스트 | `tests/test_views.py` (케이스 추가) |

---

## `views/monitoring_view.py`

### 화면 예시

```
╔══════════════════════════════════════════════════════════════╗
║                         모니터링                              ║
╚══════════════════════════════════════════════════════════════╝

┌─ 주문 현황 ──────────────────────────────────────────────────┐
  RESERVED    2건
  PRODUCING   1건
  CONFIRMED   3건
  RELEASE     5건

┌─ 재고 현황 ──────────────────────────────────────────────────┐
  ID          이름          재고   주문 대비
  ──────────────────────────────────────────────────────────
  S001        AlGaN           15   여유
  S002        GaAs             0   고갈
  S003        AlGaAs           3   부족
```

### 재고 상태 판정 기준

| 상태 | 조건 | 색상 |
|------|------|------|
| 여유 | 재고 ≥ 총 주문 수량 (RESERVED + PRODUCING) | GREEN |
| 부족 | 0 < 재고 < 총 주문 수량 | YELLOW |
| 고갈 | 재고 = 0 | RED |

### 구현

```python
from colorama import Fore
from controllers.sample_controller import SampleController
from controllers.order_controller import OrderController
from repositories.order_repository import OrderRepository
from models.order import OrderStatus
from views.common import header, section, divider


class MonitoringView:
    def __init__(self, sample_ctrl: SampleController, order_repo: OrderRepository):
        self._sample_ctrl = sample_ctrl
        self._order_repo  = order_repo

    def show(self):
        header("모니터링")
        self._show_order_summary()
        self._show_stock_status()

    def _show_order_summary(self):
        section("주문 현황")
        for status in [OrderStatus.RESERVED, OrderStatus.PRODUCING,
                       OrderStatus.CONFIRMED, OrderStatus.RELEASE]:
            count = len(self._order_repo.find_by_status(status))
            print(f"  {status.value:<12} {count}건")

    def _show_stock_status(self):
        section("재고 현황")
        samples = self._sample_ctrl.list_all()
        if not samples:
            print("  등록된 시료가 없습니다.")
            return
        print(f"  {'ID':<12} {'이름':<14} {'재고':>5}   주문 대비")
        divider()
        for s in samples:
            demand = sum(
                o.quantity for o in self._order_repo.find_all()
                if o.sample_id == s.sample_id
                and o.status in (OrderStatus.RESERVED, OrderStatus.PRODUCING)
            )
            tag, color = self._stock_tag(s.stock, demand)
            print(f"  {s.sample_id:<12} {s.name:<14} {s.stock:>5}   {color}{tag}{Fore.RESET}")

    @staticmethod
    def _stock_tag(stock: int, demand: int) -> tuple[str, str]:
        if stock == 0:
            return "고갈", Fore.RED
        if stock < demand:
            return "부족", Fore.YELLOW
        return "여유", Fore.GREEN
```

---

## `views/production_view.py`

### 화면 예시

```
╔══════════════════════════════════════════════════════════════╗
║                        생산 라인                              ║
╚══════════════════════════════════════════════════════════════╝

┌─ 현재 생산 중 ────────────────────────────────────────────────┐
  주문 ID  : a1b2c3d4…
  시료 ID  : S001
  생산 수량: 13개
  예상 시간: 26.0h

┌─ 대기 큐 (FIFO) ──────────────────────────────────────────────┐
  순서   주문 ID      시료 ID    생산 수량   예상 시간
  ──────────────────────────────────────────────────────────
  [1]    e5f6g7h8     S001          9       18.0h
  [2]    i9j0k1l2     S002          5       15.0h

  완료 처리할 주문 ID를 입력하세요 (건너뛰려면 Enter):
```

### 구현

```python
from controllers.production_controller import ProductionController
from views.common import header, section, divider, success, error, ask


class ProductionView:
    def __init__(self, ctrl: ProductionController):
        self._ctrl = ctrl

    def show(self):
        header("생산 라인")
        self._show_current()
        self._show_queue()
        self._handle_complete()

    def _show_current(self):
        section("현재 생산 중")
        job = self._ctrl.get_current_job()
        if job is None:
            print("  현재 생산 중인 작업이 없습니다.")
            return
        print(f"  주문 ID  : {job.order_id[:8]}…")
        print(f"  시료 ID  : {job.sample_id}")
        print(f"  생산 수량: {job.actual_production}개")
        print(f"  예상 시간: {job.total_time:.1f}h")

    def _show_queue(self):
        section("대기 큐 (FIFO)")
        queue = self._ctrl.list_queue()
        if not queue:
            print("  대기 중인 작업이 없습니다.")
            return
        print(f"  {'순서':<5} {'주문 ID':<14} {'시료 ID':<10} {'생산 수량':>8}  {'예상 시간':>8}")
        divider()
        for i, job in enumerate(queue, 1):
            print(f"  [{i}]   {job.order_id[:8]:<14} {job.sample_id:<10} {job.actual_production:>8}  {job.total_time:>7.1f}h")

    def _handle_complete(self):
        job = self._ctrl.get_current_job()
        if job is None:
            return
        print()
        order_id = ask("완료 처리할 주문 ID 입력 (건너뛰려면 Enter) >")
        if not order_id:
            return
        try:
            self._ctrl.complete_job(order_id)
            success("생산 완료 처리되었습니다.")
        except (ValueError, IndexError) as e:
            error(str(e))
```

---

## `views/release_view.py`

### 화면 예시

```
╔══════════════════════════════════════════════════════════════╗
║                        출고 처리                              ║
╚══════════════════════════════════════════════════════════════╝

┌─ 출고 대기 주문 ──────────────────────────────────────────────┐
  No   주문ID      시료ID    고객명        수량
  ──────────────────────────────────────────────────────────
  [1]  a1b2c3d4    S001      홍길동          10
  [2]  e5f6g7h8    S002      이순신           5

  번호 선택 > 1
  ✔ 출고 완료
```

### 구현

```python
from controllers.release_controller import ReleaseController
from views.common import header, section, divider, success, error, ask, menu_item


class ReleaseView:
    def __init__(self, ctrl: ReleaseController):
        self._ctrl = ctrl

    def show(self):
        header("출고 처리")
        confirmed = self._ctrl.list_confirmed()
        section("출고 대기 주문")
        if not confirmed:
            print("  출고 대기 중인 주문이 없습니다.")
            return
        print(f"  {'No':<5} {'주문ID':<12} {'시료ID':<8} {'고객명':<12} {'수량':>5}")
        divider()
        for i, o in enumerate(confirmed, 1):
            print(f"  [{i}]  {o.order_id[:8]:<12} {o.sample_id:<8} {o.customer:<12} {o.quantity:>5}")
        print()
        try:
            idx = int(ask("번호 선택 >")) - 1
            if not (0 <= idx < len(confirmed)):
                error("올바른 번호를 선택해주세요.")
                return
            self._ctrl.release(confirmed[idx].order_id)
            success("출고 완료")
        except (ValueError, IndexError) as e:
            error(str(e))
```

---

## 테스트 추가 — `tests/test_views.py`

```python
# ── MonitoringView ────────────────────────────────────────────
class TestMonitoringView:
    def test_shows_order_status_counts(self, monkeypatch, capsys, ...):
        # 각 상태별 주문 생성 후 show() 호출
        # RESERVED, PRODUCING 등 상태명이 출력에 포함되는지 확인
        ...

    def test_stock_tag_여유(self, ...):
        # 재고 충분 → "여유" 출력
        ...

    def test_stock_tag_고갈(self, ...):
        # 재고 0 → "고갈" 출력
        ...


# ── ProductionView ────────────────────────────────────────────
class TestProductionView:
    def test_shows_no_job_message_when_queue_empty(self, monkeypatch, capsys, ...):
        # 빈 큐일 때 "현재 생산 중인 작업이 없습니다" 출력 확인
        ...

    def test_shows_current_job_info(self, ...):
        # 큐에 Job 있을 때 order_id, sample_id 출력 확인
        ...


# ── ReleaseView ───────────────────────────────────────────────
class TestReleaseView:
    def test_shows_no_confirmed_message(self, monkeypatch, capsys, ...):
        # CONFIRMED 주문 없을 때 메시지 출력 확인
        ...

    def test_release_success_prints_confirmation(self, ...):
        # 출고 처리 후 "✔ 출고 완료" 출력 확인
        ...
```

---

## 수동 검증 시나리오

1. 모니터링 화면에서 상태별 주문 수가 정확히 표시되는지 확인
2. 재고 상태 태그(여유/부족/고갈) 색상이 올바르게 표시되는지 확인
3. 생산 라인에서 현재 작업 정보 및 대기 큐가 순서대로 표시되는지 확인
4. 출고 처리 후 목록에서 해당 주문이 사라지는지 확인

---

## 체크리스트

- [ ] `views/monitoring_view.py` 구현
- [ ] `views/production_view.py` 구현
- [ ] `views/release_view.py` 구현
- [ ] `tests/test_views.py` 케이스 추가 및 통과
- [ ] 수동 검증 시나리오 1~4 통과
