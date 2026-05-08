import uuid
from models.order import Order, OrderStatus
from repositories.order_repository import OrderRepository
from repositories.sample_repository import SampleRepository


class OrderController:
    def __init__(self, sample_repo: SampleRepository, order_repo: OrderRepository):
        self._sample_repo = sample_repo
        self._order_repo  = order_repo

    def reserve(self, sample_id: str, customer: str, quantity: int) -> Order:
        if self._sample_repo.find_by_id(sample_id) is None:
            raise ValueError(f"등록되지 않은 시료입니다: {sample_id}")
        order = Order(
            order_id=str(uuid.uuid4()),
            sample_id=sample_id,
            customer=customer,
            quantity=quantity,
        )
        self._order_repo.save(order)
        return order

    def list_reserved(self) -> list[Order]:
        return self._order_repo.find_by_status(OrderStatus.RESERVED)

    def reject(self, order_id: str) -> None:
        order = self._order_repo.find_by_id(order_id)
        if order is None:
            raise ValueError(f"존재하지 않는 주문입니다: {order_id}")
        order.status = OrderStatus.REJECTED
        self._order_repo.save(order)
