from pathlib import Path
from models.order import Order, OrderStatus
from repositories.json_repository import load, save


class OrderRepository:
    def __init__(self, filepath):
        self._filepath = Path(filepath)

    def find_all(self) -> list[Order]:
        data = load(self._filepath)
        return [self._to_order(d) for d in data] if data else []

    def find_by_id(self, order_id: str) -> Order | None:
        return next((o for o in self.find_all() if o.order_id == order_id), None)

    def find_by_status(self, status: OrderStatus) -> list[Order]:
        return [o for o in self.find_all() if o.status == status]

    def save(self, order: Order) -> None:
        all_orders = self.find_all()
        updated = [o for o in all_orders if o.order_id != order.order_id]
        updated.append(order)
        save(self._filepath, [self._to_dict(o) for o in updated])

    def _to_dict(self, o: Order) -> dict:
        return {
            "order_id": o.order_id,
            "sample_id": o.sample_id,
            "customer": o.customer,
            "quantity": o.quantity,
            "status": o.status.value,
        }

    def _to_order(self, d: dict) -> Order:
        order = Order(
            order_id=d["order_id"],
            sample_id=d["sample_id"],
            customer=d["customer"],
            quantity=d["quantity"],
        )
        order.status = OrderStatus(d["status"])
        return order
