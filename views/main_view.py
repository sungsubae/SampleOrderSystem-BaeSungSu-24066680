from controllers.sample_controller import SampleController
from controllers.order_controller import OrderController
from controllers.production_controller import ProductionController
from controllers.release_controller import ReleaseController
from views.common import header, section, success, error, ask, menu_item
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
        self._sample_ctrl = sample_ctrl
        self._sample_view = SampleView(sample_ctrl)
        self._order_view  = OrderView(order_ctrl)

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
