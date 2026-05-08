# Phase 10 세부 설계 — main.py 통합

> TDD 순서: 테스트 작성(Red) → 구현(Green) → 전체 테스트 통과 확인 → 리팩토링 → 전체 테스트 통과 확인

---

## 대상 파일

| 구분 | 파일 |
|------|------|
| 구현 | `main.py` |
| 테스트 | `tests/test_views.py` (`TestMainView` 케이스 추가) |

---

## 역할

`main.py`는 애플리케이션 진입점으로, 모든 Repository·Controller·View 인스턴스를 생성하고 연결한다.

```
main.py
  └── Repository 초기화 (data/*.json)
        ├── SampleRepository
        ├── OrderRepository
        └── ProductionRepository
  └── Controller 초기화
        ├── SampleController(sample_repo)
        ├── OrderController(sample_repo, order_repo, production_repo)
        ├── ProductionController(production_repo, order_repo, sample_repo)
        └── ReleaseController(order_repo)
  └── View 초기화
        └── MainView(sample_ctrl, order_ctrl, production_ctrl, release_ctrl)
              ├── SampleView
              ├── OrderView
              ├── MonitoringView  ← Phase 9에서 추가
              ├── ProductionView  ← Phase 9에서 추가
              └── ReleaseView     ← Phase 9에서 추가
  └── MainView.run()
```

---

## `main.py` 구현

```python
from pathlib import Path

from repositories.sample_repository import SampleRepository
from repositories.order_repository import OrderRepository
from repositories.production_repository import ProductionRepository
from controllers.sample_controller import SampleController
from controllers.order_controller import OrderController
from controllers.production_controller import ProductionController
from controllers.release_controller import ReleaseController
from views.main_view import MainView


DATA_DIR = Path("data")


def build_main_view() -> MainView:
    DATA_DIR.mkdir(exist_ok=True)

    sample_repo     = SampleRepository(DATA_DIR / "samples.json")
    order_repo      = OrderRepository(DATA_DIR / "orders.json")
    production_repo = ProductionRepository(DATA_DIR / "production_queue.json")

    sample_ctrl     = SampleController(sample_repo)
    order_ctrl      = OrderController(sample_repo, order_repo, production_repo)
    production_ctrl = ProductionController(production_repo, order_repo, sample_repo)
    release_ctrl    = ReleaseController(order_repo)

    return MainView(sample_ctrl, order_ctrl, production_ctrl, release_ctrl)


if __name__ == "__main__":
    build_main_view().run()
```

---

## `main_view.py` 업데이트 — Phase 9 View 연결

Phase 8에서 3·4·5번 메뉴를 플레이스홀더로 남겨뒀으므로, Phase 9에서 구현된 View를 연결한다.

```python
class MainView:
    def __init__(self, sample_ctrl, order_ctrl, production_ctrl, release_ctrl):
        ...
        self._monitoring_view = MonitoringView(sample_ctrl, order_repo)  # order_repo 직접 접근 필요
        self._production_view = ProductionView(production_ctrl)
        self._release_view    = ReleaseView(release_ctrl)

    def run(self):
        while True:
            ...
            elif choice == "3":
                self._monitoring_view.show()
            elif choice == "4":
                self._release_view.show()
            elif choice == "5":
                self._production_view.show()
```

> `MonitoringView`는 `OrderRepository`를 직접 받으므로, `MainView` 생성자에서  
> `order_ctrl._order_repo`를 통해 접근하거나, `order_repo`를 별도로 주입한다.  
> **권장**: `order_repo`를 `MainView` 생성자 파라미터로 추가한다.

---

## `MainView` 생성자 변경

```python
class MainView:
    def __init__(
        self,
        sample_ctrl: SampleController,
        order_ctrl: OrderController,
        production_ctrl: ProductionController,
        release_ctrl: ReleaseController,
        order_repo,          # MonitoringView에 주입
    ):
```

---

## 테스트 — `tests/test_views.py` (`TestMainView` 추가)

```python
class TestMainView:
    def test_menu_routes_to_sample_view(self, monkeypatch, capsys, ctrls):
        sample_ctrl, order_ctrl, production_ctrl, release_ctrl, order_repo = ctrls
        inputs = iter(["1", "0", "0"])  # 메인 → 시료 관리 → 돌아가기 → 종료
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        MainView(sample_ctrl, order_ctrl, production_ctrl, release_ctrl, order_repo).run()
        out = capsys.readouterr().out
        assert "시료 관리" in out

    def test_menu_routes_to_order_view(self, monkeypatch, capsys, ctrls):
        sample_ctrl, order_ctrl, production_ctrl, release_ctrl, order_repo = ctrls
        inputs = iter(["2", "0", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        MainView(sample_ctrl, order_ctrl, production_ctrl, release_ctrl, order_repo).run()
        out = capsys.readouterr().out
        assert "주문 관리" in out

    def test_menu_routes_to_monitoring_view(self, monkeypatch, capsys, ctrls):
        sample_ctrl, order_ctrl, production_ctrl, release_ctrl, order_repo = ctrls
        inputs = iter(["3", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        MainView(sample_ctrl, order_ctrl, production_ctrl, release_ctrl, order_repo).run()
        out = capsys.readouterr().out
        assert "모니터링" in out

    def test_menu_routes_to_release_view(self, monkeypatch, capsys, ctrls):
        sample_ctrl, order_ctrl, production_ctrl, release_ctrl, order_repo = ctrls
        inputs = iter(["4", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        MainView(sample_ctrl, order_ctrl, production_ctrl, release_ctrl, order_repo).run()
        out = capsys.readouterr().out
        assert "출고 처리" in out

    def test_menu_routes_to_production_view(self, monkeypatch, capsys, ctrls):
        sample_ctrl, order_ctrl, production_ctrl, release_ctrl, order_repo = ctrls
        inputs = iter(["5", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        MainView(sample_ctrl, order_ctrl, production_ctrl, release_ctrl, order_repo).run()
        out = capsys.readouterr().out
        assert "생산 라인" in out

    def test_exit_prints_message(self, monkeypatch, capsys, ctrls):
        sample_ctrl, order_ctrl, production_ctrl, release_ctrl, order_repo = ctrls
        monkeypatch.setattr("builtins.input", lambda _: "0")
        MainView(sample_ctrl, order_ctrl, production_ctrl, release_ctrl, order_repo).run()
        out = capsys.readouterr().out
        assert "종료" in out

    def test_invalid_choice_shows_error(self, monkeypatch, capsys, ctrls):
        sample_ctrl, order_ctrl, production_ctrl, release_ctrl, order_repo = ctrls
        inputs = iter(["9", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        MainView(sample_ctrl, order_ctrl, production_ctrl, release_ctrl, order_repo).run()
        out = capsys.readouterr().out
        assert "올바른 메뉴를 선택해주세요" in out
```

---

## 통합 시나리오 (수동 검증)

```bash
python main.py
```

| 시나리오 | 단계 |
|----------|------|
| 1. 재고 부족 흐름 | 시료 등록 → 주문 접수 → 승인(재고 부족) → 생산 라인에서 완료 처리 → 출고 |
| 2. 재고 충분 흐름 | 시료 등록(재고 설정) → 주문 접수 → 승인(재고 충분) → 출고 |
| 3. 거절 흐름 | 주문 접수 → 거절 → 모니터링에서 REJECTED 미노출 확인 |

---

## 체크리스트

- [ ] `main_view.py` Phase 9 View 연결 (`order_repo` 파라미터 추가)
- [ ] `main.py` 진입점 구현
- [ ] `tests/test_views.py` `TestMainView` 7개 케이스 추가 및 통과
- [ ] 통합 시나리오 1·2·3 수동 검증 완료
