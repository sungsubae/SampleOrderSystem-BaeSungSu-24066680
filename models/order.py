from dataclasses import dataclass
from enum import Enum


class OrderStatus(Enum):
    RESERVED  = "RESERVED"
    REJECTED  = "REJECTED"
    PRODUCING = "PRODUCING"
    CONFIRMED = "CONFIRMED"
    RELEASE   = "RELEASE"


@dataclass
class Order:
    order_id: str
    sample_id: str
    customer: str
    quantity: int
    status: OrderStatus = OrderStatus.RESERVED
