from models.order import OrderStatus
from repositories.order_repository import OrderRepository
from repositories.production_repository import ProductionRepository
from repositories.sample_repository import SampleRepository


class ProductionController:
    def __init__(
        self,
        production_repo: ProductionRepository,
        order_repo: OrderRepository,
        sample_repo: SampleRepository,
    ):
        self._production_repo = production_repo
        self._order_repo      = order_repo
        self._sample_repo     = sample_repo

    def get_current_job(self):
        return self._production_repo.load().peek()

    def list_queue(self) -> list:
        return self._production_repo.load().to_list()

    def complete_job(self, order_id: str) -> None:
        queue = self._production_repo.load()
        job = queue.dequeue()
        if job.order_id != order_id:
            raise ValueError(f"현재 생산 중인 주문이 아닙니다: {order_id}")

        sample = self._sample_repo.find_by_id(job.sample_id)
        sample.stock += job.actual_production
        self._sample_repo.save(sample)

        order = self._order_repo.find_by_id(job.order_id)
        order.status = OrderStatus.CONFIRMED
        self._order_repo.save(order)

        self._production_repo.save(queue)
