from controllers.order_controller import OrderController
from views.common import header, section, divider, success, error, ask, ask_int, menu_item


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
            quantity  = ask_int("수량     >")
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
