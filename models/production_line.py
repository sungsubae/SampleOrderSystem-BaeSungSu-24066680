from __future__ import annotations
from collections import deque
from dataclasses import dataclass


@dataclass
class ProductionJob:
    order_id: str
    sample_id: str
    actual_production: int
    total_time: float
    produced_so_far: int = 0


class ProductionQueue:
    def __init__(self):
        self._queue: deque[ProductionJob] = deque()

    def enqueue(self, job: ProductionJob) -> None:
        self._queue.append(job)

    def dequeue(self) -> ProductionJob:
        if self.is_empty():
            raise IndexError("생산 큐가 비어 있습니다.")
        return self._queue.popleft()

    def peek(self) -> ProductionJob | None:
        return self._queue[0] if self._queue else None

    def size(self) -> int:
        return len(self._queue)

    def is_empty(self) -> bool:
        return len(self._queue) == 0

    def to_list(self) -> list[ProductionJob]:
        return list(self._queue)
