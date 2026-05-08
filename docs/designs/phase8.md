# Phase 8 세부 설계 — View (메인·시료·주문)

> TDD 순서: 테스트 작성(Red) → 구현(Green) → 전체 테스트 통과 확인 → 리팩토링 → 전체 테스트 통과 확인

> View는 콘솔 I/O를 직접 다루므로 단위 테스트 적용이 제한적이다.  
> 구현 완료 후 수동으로 골든 패스(정상 흐름)를 검증한다.

---

## 대상 파일

| 구분 | 파일 |
|------|------|
| 구현 | `views/__init__.py` |
| 구현 | `views/common.py` |
| 구현 | `views/main_view.py` |
| 구현 | `views/sample_view.py` |
| 구현 | `views/order_view.py` |

---

## 설계 원칙

- **View는 입출력만 담당** — 비즈니스 로직은 Controller에 위임한다.
- **입력**: `input()` 로 사용자 입력 수집, 유효하지 않은 값은 재입력 요청
- **출력**: `colorama`로 컬러 강조, 일관된 테두리 스타일 사용
- **Controller 주입**: View 생성자에서 필요한 Controller를 받아 저장

---

## `views/common.py` — 공통 유틸

모든 View에서 재사용하는 출력 헬퍼를 모아둔다.

```python
from colorama import init, Fore, Style

init(autoreset=True)

WIDTH = 62


def header(title: str):
    print()
    print(Fore.CYAN + "╔" + "═" * WIDTH + "╗")
    print(Fore.CYAN + "║" + title.center(WIDTH) + "║")
    print(Fore.CYAN + "╚" + "═" * WIDTH + "╝")


def section(title: str):
    print()
    print(Fore.YELLOW + f"┌─ {title} " + "─" * (WIDTH - len(title) - 3) + "┐")


def success(msg: str):
    print(Fore.GREEN + f"  ✔ {msg}")


def error(msg: str):
    print(Fore.RED + f"  ✖ {msg}")


def divider():
    print(Fore.WHITE + Style.DIM + "  " + "─" * (WIDTH - 2))


def ask(prompt: str) -> str:
    return input(Fore.WHITE + f"  {prompt} ").strip()


def ask_int(prompt: str) -> int:
    while True:
        try:
            return int(ask(prompt))
        except ValueError:
            error("숫자를 입력해주세요.")


def ask_float(prompt: str) -> float:
    while True:
        try:
            return float(ask(prompt))
        except ValueError:
            error("숫자를 입력해주세요.")


def menu_item(num: int | str, label: str):
    print(f"  {Fore.CYAN}[{num}]{Style.RESET_ALL} {label}")
```

---

## `views/main_view.py`

### 화면 예시

```
╔══════════════════════════════════════════════════════════════╗
║            반도체 시료 생산주문관리 시스템  —  S-Semi           ║
╚══════════════════════════════════════════════════════════════╝

┌─ 시료 현황 ──────────────────────────────────────────────────┐
  등록 시료: 3개   |   총 재고: 42개

  [1] 시료 관리
  [2] 주문 (접수 / 승인 / 거절)
  [3] 모니터링
  [4] 출고 처리
  [5] 생산 라인
  [0] 종료

  선택 > _
```

### 구현

```python
from views.common import header, section, menu_item, ask, error, success
from controllers.sample_controller import SampleController
from controllers.order_controller import OrderController
from controllers.production_controller import ProductionController
from controllers.release_controller import ReleaseController
from views.sample_view import SampleView
from views.order_view import OrderView


class MainView:
    def __init__(
        self,
        sample_ctrl: SampleController,
        order_ctrl: OrderController,
        production_ctrl: ProductionController,
        release_ctrl: ReleaseController,
    ):
        self._sample_ctrl    = sample_ctrl
        self._sample_view    = SampleView(sample_ctrl)
        self._order_view     = OrderView(order_ctrl)
        # Phase 9에서 추가: MonitoringView, ProductionView, ReleaseView

    def run(self):
        while True:
            self._render()
            choice = ask("선택 >")
            if choice == "1":
                self._sample_view.menu()
            elif choice == "2":
                self._order_view.menu()
            elif choice == "3":
                print("  [모니터링] Phase 9에서 구현 예정")
            elif choice == "4":
                print("  [출고 처리] Phase 9에서 구현 예정")
            elif choice == "5":
                print("  [생산 라인] Phase 9에서 구현 예정")
            elif choice == "0":
                success("시스템을 종료합니다.")
                break
            else:
                error("올바른 메뉴를 선택해주세요.")

    def _render(self):
        samples = self._sample_ctrl.list_all()
        total_stock = sum(s.stock for s in samples)
        header("반도체 시료 생산주문관리 시스템  —  S-Semi")
        section("시료 현황")
        print(f"  등록 시료: {len(samples)}개   |   총 재고: {total_stock}개")
        print()
        menu_item(1, "시료 관리")
        menu_item(2, "주문 (접수 / 승인 / 거절)")
        menu_item(3, "모니터링")
        menu_item(4, "출고 처리")
        menu_item(5, "생산 라인")
        menu_item(0, "종료")
        print()
```

---

## `views/sample_view.py`

### 시료 목록 화면 예시

```
┌─ 시료 목록 ──────────────────────────────────────────────────┐
  ID          이름          생산시간    수율    재고
  ──────────────────────────────────────────────────────────
  S001        AlGaN         2.0h      90.0%     15
  S002        GaAs          3.0h      80.0%      0
  S003        AlGaAs        4.0h      70.0%    100
```

### 구현

```python
from views.common import header, section, divider, success, error, ask, ask_float
from controllers.sample_controller import SampleController


class SampleView:
    def __init__(self, ctrl: SampleController):
        self._ctrl = ctrl

    def menu(self):
        while True:
            header("시료 관리")
            menu_item(1, "시료 등록")
            menu_item(2, "시료 목록 조회")
            menu_item(3, "시료 검색")
            menu_item(0, "돌아가기")
            print()
            choice = ask("선택 >")
            if choice == "1":
                self._register()
            elif choice == "2":
                self._list_all()
            elif choice == "3":
                self._search()
            elif choice == "0":
                break
            else:
                error("올바른 메뉴를 선택해주세요.")

    def _register(self):
        header("시료 등록")
        try:
            sample_id  = ask("시료 ID       >")
            name       = ask("이름          >")
            avg_time   = ask_float("평균 생산시간(h)>")
            yield_rate = ask_float("수율 (0 초과 1 이하)>")
            self._ctrl.register(sample_id=sample_id, name=name, avg_time=avg_time, yield_rate=yield_rate)
            success(f"시료 '{name}' 등록 완료")
        except ValueError as e:
            error(str(e))

    def _list_all(self):
        samples = self._ctrl.list_all()
        section("시료 목록")
        if not samples:
            print("  등록된 시료가 없습니다.")
            return
        print(f"  {'ID':<12} {'이름':<14} {'생산시간':>8}  {'수율':>6}  {'재고':>5}")
        divider()
        for s in samples:
            print(f"  {s.sample_id:<12} {s.name:<14} {s.avg_production_time:>6.1f}h  {s.yield_rate*100:>5.1f}%  {s.stock:>5}")

    def _search(self):
        header("시료 검색")
        keyword = ask("검색어 >")
        results = self._ctrl.search(keyword)
        section(f"검색 결과 — '{keyword}'")
        if not results:
            print("  검색 결과가 없습니다.")
            return
        print(f"  {'ID':<12} {'이름':<14} {'재고':>5}")
        divider()
        for s in results:
            print(f"  {s.sample_id:<12} {s.name:<14} {s.stock:>5}")
```

---

## `views/order_view.py`

### 접수된 주문 목록 화면 예시

```
┌─ 접수된 주문 목록 ────────────────────────────────────────────┐
  No   주문ID      시료ID    고객명        수량
  ──────────────────────────────────────────────────────────
  [1]  a1b2c3d4    S001      홍길동          10
  [2]  e5f6g7h8    S001      이순신           5

  번호 선택 > 1
  승인(a) / 거절(r) > a
  ✔ 주문 승인 완료
```

### 구현

```python
from views.common import header, section, divider, success, error, ask
from controllers.order_controller import OrderController


class OrderView:
    def __init__(self, ctrl: OrderController):
        self._ctrl = ctrl

    def menu(self):
        while True:
            header("주문 관리")
            menu_item(1, "주문 접수")
            menu_item(2, "주문 승인 / 거절")
            menu_item(0, "돌아가기")
            print()
            choice = ask("선택 >")
            if choice == "1":
                self._reserve()
            elif choice == "2":
                self._approve_or_reject()
            elif choice == "0":
                break
            else:
                error("올바른 메뉴를 선택해주세요.")

    def _reserve(self):
        header("주문 접수")
        try:
            sample_id = ask("시료 ID  >")
            customer  = ask("고객명   >")
            quantity  = int(ask("수량     >"))
            order = self._ctrl.reserve(sample_id=sample_id, customer=customer, quantity=quantity)
            success(f"주문 접수 완료  (ID: {order.order_id[:8]}…)")
        except ValueError as e:
            error(str(e))

    def _approve_or_reject(self):
        reserved = self._ctrl.list_reserved()
        section("접수된 주문 목록")
        if not reserved:
            print("  접수된 주문이 없습니다.")
            return
        print(f"  {'No':<5} {'주문ID':<12} {'시료ID':<8} {'고객명':<12} {'수량':>5}")
        divider()
        for i, o in enumerate(reserved, 1):
            print(f"  [{i}]  {o.order_id[:8]:<12} {o.sample_id:<8} {o.customer:<12} {o.quantity:>5}")
        print()
        try:
            idx = int(ask("번호 선택 >")) - 1
            if not (0 <= idx < len(reserved)):
                error("올바른 번호를 선택해주세요.")
                return
            order = reserved[idx]
            action = ask("승인(a) / 거절(r) >").lower()
            if action == "a":
                self._ctrl.approve(order.order_id)
                success("주문 승인 완료")
            elif action == "r":
                self._ctrl.reject(order.order_id)
                success("주문 거절 완료")
            else:
                error("올바른 선택이 아닙니다.")
        except (ValueError, IndexError) as e:
            error(str(e))
```

---

## 테스트 전략

### pexpect 사용 불가 이유

`pexpect`는 Unix PTY(가상 터미널)에 의존하므로 **Windows에서 동작하지 않는다**.

### 대안: `monkeypatch` + `capsys` (pytest 내장)

`input()`을 모킹하고 `print()` 출력을 캡처하는 방식으로 View를 자동 테스트한다.
- Windows 완전 지원
- subprocess 없이 in-process 실행 → 빠르고 결정적
- colorama ANSI 코드가 포함된 출력도 검증 가능

### `tests/test_views.py`

```python
import pytest
from controllers.sample_controller import SampleController
from controllers.order_controller import OrderController
from repositories.sample_repository import SampleRepository
from repositories.order_repository import OrderRepository
from repositories.production_repository import ProductionRepository
from models.sample import Sample
from views.sample_view import SampleView
from views.order_view import OrderView


@pytest.fixture
def sample_ctrl(tmp_path):
    repo = SampleRepository(tmp_path / "samples.json")
    return SampleController(repo)


@pytest.fixture
def order_ctrl(tmp_path):
    sample_repo     = SampleRepository(tmp_path / "samples.json")
    order_repo      = OrderRepository(tmp_path / "orders.json")
    production_repo = ProductionRepository(tmp_path / "production_queue.json")
    sample_repo.save(Sample(sample_id="S001", name="AlGaN", avg_production_time=2.0, yield_rate=0.9, stock=10))
    return OrderController(sample_repo=sample_repo, order_repo=order_repo, production_repo=production_repo)


# ── SampleView ────────────────────────────────────────────────
class TestSampleView:
    def test_register_success_prints_confirmation(self, monkeypatch, capsys, sample_ctrl):
        inputs = iter(["S001", "AlGaN", "2.0", "0.9", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        view = SampleView(sample_ctrl)
        view.menu()
        out = capsys.readouterr().out
        assert "AlGaN" in out
        assert "✔" in out

    def test_register_duplicate_id_prints_error(self, monkeypatch, capsys, sample_ctrl):
        sample_ctrl.register(sample_id="S001", name="AlGaN", avg_time=2.0, yield_rate=0.9)
        inputs = iter(["S001", "AlGaN", "2.0", "0.9", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        view = SampleView(sample_ctrl)
        view.menu()
        out = capsys.readouterr().out
        assert "✖" in out

    def test_list_all_shows_registered_samples(self, monkeypatch, capsys, sample_ctrl):
        sample_ctrl.register(sample_id="S001", name="AlGaN", avg_time=2.0, yield_rate=0.9)
        inputs = iter(["2", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        view = SampleView(sample_ctrl)
        view.menu()
        out = capsys.readouterr().out
        assert "S001" in out
        assert "AlGaN" in out

    def test_search_returns_matching(self, monkeypatch, capsys, sample_ctrl):
        sample_ctrl.register(sample_id="S001", name="AlGaN", avg_time=2.0, yield_rate=0.9)
        sample_ctrl.register(sample_id="S002", name="GaAs",  avg_time=3.0, yield_rate=0.8)
        inputs = iter(["3", "Al", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        view = SampleView(sample_ctrl)
        view.menu()
        out = capsys.readouterr().out
        assert "AlGaN" in out
        assert "GaAs" not in out

    def test_invalid_yield_rate_shows_error(self, monkeypatch, capsys, sample_ctrl):
        inputs = iter(["S001", "AlGaN", "2.0", "abc", "0.9", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        view = SampleView(sample_ctrl)
        view.menu()
        out = capsys.readouterr().out
        assert "숫자를 입력해주세요" in out


# ── OrderView ─────────────────────────────────────────────────
class TestOrderView:
    def test_reserve_success_prints_confirmation(self, monkeypatch, capsys, order_ctrl):
        inputs = iter(["1", "S001", "홍길동", "5", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        view = OrderView(order_ctrl)
        view.menu()
        out = capsys.readouterr().out
        assert "✔" in out

    def test_reserve_unknown_sample_prints_error(self, monkeypatch, capsys, order_ctrl):
        inputs = iter(["1", "NONE", "홍길동", "5", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        view = OrderView(order_ctrl)
        view.menu()
        out = capsys.readouterr().out
        assert "✖" in out

    def test_approve_order_prints_confirmation(self, monkeypatch, capsys, order_ctrl):
        order_ctrl.reserve(sample_id="S001", customer="홍길동", quantity=5)
        inputs = iter(["2", "1", "a", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        view = OrderView(order_ctrl)
        view.menu()
        out = capsys.readouterr().out
        assert "✔" in out

    def test_no_reserved_orders_shows_message(self, monkeypatch, capsys, order_ctrl):
        inputs = iter(["2", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        view = OrderView(order_ctrl)
        view.menu()
        out = capsys.readouterr().out
        assert "접수된 주문이 없습니다" in out
```

---

## 수동 검증 시나리오

1. 시료 등록 → 목록 조회에서 확인, 컬럼 정렬 확인
2. 주문 접수 → 승인/거절 목록에서 확인 → 승인(a) 처리
3. 잘못된 입력(문자 → 숫자 필드) 시 `✖ 숫자를 입력해주세요.` 출력 후 재입력
4. 메뉴 `0` 선택 시 상위 메뉴로 복귀
5. 컬러 출력 확인 (헤더: CYAN, 성공: GREEN, 오류: RED, 섹션: YELLOW)

---

## 체크리스트

- [ ] `views/__init__.py` 생성
- [ ] `views/common.py` 공통 유틸 구현
- [ ] `views/main_view.py` 메뉴 루프 구현
- [ ] `views/sample_view.py` 구현
- [ ] `views/order_view.py` 구현
- [ ] `tests/test_views.py` 작성 및 통과
- [ ] 수동 검증 시나리오 1~5 통과
