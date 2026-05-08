from colorama import Fore
from controllers.sample_controller import SampleController
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
        active_orders = [
            o for o in self._order_repo.find_all()
            if o.status in (OrderStatus.RESERVED, OrderStatus.PRODUCING)
        ]
        print(f"  {'ID':<12} {'이름':<14} {'재고':>5}   주문 대비")
        divider()
        for s in samples:
            demand = sum(o.quantity for o in active_orders if o.sample_id == s.sample_id)
            tag, color = self._stock_tag(s.stock, demand)
            print(f"  {s.sample_id:<12} {s.name:<14} {s.stock:>5}   {color}{tag}{Fore.RESET}")

    @staticmethod
    def _stock_tag(stock: int, demand: int) -> tuple[str, str]:
        if stock == 0:
            return "고갈", Fore.RED
        if stock < demand:
            return "부족", Fore.YELLOW
        return "여유", Fore.GREEN
