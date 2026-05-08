from models.order import Order, OrderStatus
from repositories.order_repository import OrderRepository


class ReleaseController:
    def __init__(self, order_repo: OrderRepository):
        self._order_repo = order_repo

    def list_confirmed(self) -> list[Order]:
        return self._order_repo.find_by_status(OrderStatus.CONFIRMED)

    def release(self, order_id: str) -> None:
        order = self._order_repo.find_by_id(order_id)
        if order is None:
            raise ValueError(f"존재하지 않는 주문입니다: {order_id}")
        if order.status != OrderStatus.CONFIRMED:
            raise ValueError(f"CONFIRMED 상태의 주문만 출고할 수 있습니다: {order.status.value}")
        order.status = OrderStatus.RELEASE
        self._order_repo.save(order)
