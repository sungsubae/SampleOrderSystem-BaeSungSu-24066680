import math
import uuid
from models.order import Order, OrderStatus
from models.production_line import ProductionJob
from repositories.order_repository import OrderRepository
from repositories.production_repository import ProductionRepository
from repositories.sample_repository import SampleRepository


class OrderController:
    def __init__(self, sample_repo: SampleRepository, order_repo: OrderRepository, production_repo: ProductionRepository = None):
        self._sample_repo     = sample_repo
        self._order_repo      = order_repo
        self._production_repo = production_repo

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
        order = self._find_order_or_raise(order_id)
        order.status = OrderStatus.REJECTED
        self._order_repo.save(order)

    def approve(self, order_id: str) -> None:
        order = self._find_order_or_raise(order_id)
        sample = self._sample_repo.find_by_id(order.sample_id)

        if sample.stock >= order.quantity:
            order.status = OrderStatus.CONFIRMED
            self._order_repo.save(order)
        else:
            shortage   = order.quantity - sample.stock
            actual     = math.ceil(shortage / (sample.yield_rate * 0.9))
            total_time = sample.avg_production_time * actual
            job = ProductionJob(
                order_id=order.order_id,
                sample_id=order.sample_id,
                actual_production=actual,
                total_time=total_time,
            )
            queue = self._production_repo.load()
            queue.enqueue(job)
            self._production_repo.save(queue)
            order.status = OrderStatus.PRODUCING
            self._order_repo.save(order)

    def _find_order_or_raise(self, order_id: str) -> Order:
        order = self._order_repo.find_by_id(order_id)
        if order is None:
            raise ValueError(f"존재하지 않는 주문입니다: {order_id}")
        return order
