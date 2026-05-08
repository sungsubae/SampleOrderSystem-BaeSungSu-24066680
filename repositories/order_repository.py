from models.order import Order, OrderStatus
from repositories.base_repository import BaseRepository


class OrderRepository(BaseRepository):
    def find_by_status(self, status: OrderStatus) -> list[Order]:
        return [o for o in self.find_all() if o.status == status]

    def _id_of(self, entity: Order) -> str:
        return entity.order_id

    def _to_dict(self, o: Order) -> dict:
        return {
            "order_id": o.order_id,
            "sample_id": o.sample_id,
            "customer": o.customer,
            "quantity": o.quantity,
            "status": o.status.value,
        }

    def _from_dict(self, d: dict) -> Order:
        order = Order(
            order_id=d["order_id"],
            sample_id=d["sample_id"],
            customer=d["customer"],
            quantity=d["quantity"],
        )
        order.status = OrderStatus(d["status"])
        return order
