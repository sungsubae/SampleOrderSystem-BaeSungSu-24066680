from controllers.sample_controller import SampleController
from controllers.order_controller import OrderController
from controllers.production_controller import ProductionController
from controllers.release_controller import ReleaseController
from repositories.order_repository import OrderRepository
from views.common import header, section, success, error, ask, menu_item
from views.sample_view import SampleView
from views.order_view import OrderView
from views.monitoring_view import MonitoringView
from views.production_view import ProductionView
from views.release_view import ReleaseView


class MainView:
    def __init__(
        self,
        sample_ctrl: SampleController,
        order_ctrl: OrderController,
        production_ctrl: ProductionController,
        release_ctrl: ReleaseController,
        order_repo: OrderRepository,
    ):
        self._sample_ctrl      = sample_ctrl
        self._sample_view      = SampleView(sample_ctrl)
        self._order_view       = OrderView(order_ctrl)
        self._monitoring_view  = MonitoringView(sample_ctrl, order_repo)
        self._production_view  = ProductionView(production_ctrl)
        self._release_view     = ReleaseView(release_ctrl)

    def run(self):
        while True:
            self._render()
            choice = ask("선택 >")
            if choice == "1":
                self._sample_view.menu()
            elif choice == "2":
                self._order_view.menu()
            elif choice == "3":
                self._monitoring_view.show()
            elif choice == "4":
                self._release_view.show()
            elif choice == "5":
                self._production_view.show()
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
