from pathlib import Path
from models.production_line import ProductionJob, ProductionQueue
from repositories.json_repository import load, save


class ProductionRepository:
    def __init__(self, filepath):
        self._filepath = Path(filepath)

    def load(self) -> ProductionQueue:
        data = load(self._filepath)
        queue = ProductionQueue()
        for d in data:
            queue.enqueue(self._to_job(d))
        return queue

    def save(self, queue: ProductionQueue) -> None:
        save(self._filepath, [self._to_dict(j) for j in queue.to_list()])

    def _to_dict(self, j: ProductionJob) -> dict:
        return {
            "order_id": j.order_id,
            "sample_id": j.sample_id,
            "actual_production": j.actual_production,
            "total_time": j.total_time,
            "produced_so_far": j.produced_so_far,
        }

    def _to_job(self, d: dict) -> ProductionJob:
        return ProductionJob(
            order_id=d["order_id"],
            sample_id=d["sample_id"],
            actual_production=d["actual_production"],
            total_time=d["total_time"],
            produced_so_far=d["produced_so_far"],
        )
