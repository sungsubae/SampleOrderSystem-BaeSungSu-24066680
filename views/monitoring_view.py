from colorama import Fore
from controllers.sample_controller import SampleController
from repositories.order_repository import OrderRepository
from models.order import OrderStatus
from views.common import header, section, divider, col


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
            orders = self._order_repo.find_by_status(status)
            print(f"\n  ▶ {status.value}  ({len(orders)}건)")
            if orders:
                print(f"  {col('주문ID',12)} {col('시료ID',8)} {col('고객명',12)} {'수량':>5}")
                divider()
                for o in orders:
                    print(f"  {col(o.order_id[:8],12)} {col(o.sample_id,8)} {col(o.customer,12)} {o.quantity:>5}")

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
        print(f"  {col('ID',12)} {col('이름',14)} {'재고':>5}   주문 대비")
        divider()
        for s in samples:
            demand = sum(o.quantity for o in active_orders if o.sample_id == s.sample_id)
            tag, color = self._stock_tag(s.stock, demand)
            print(f"  {col(s.sample_id,12)} {col(s.name,14)} {s.stock:>5}   {color}{tag}{Fore.RESET}")

    @staticmethod
    def _stock_tag(stock: int, demand: int) -> tuple[str, str]:
        if stock == 0:
            return "고갈", Fore.RED
        if stock < demand:
            return "부족", Fore.YELLOW
        return "여유", Fore.GREEN
