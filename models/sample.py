from dataclasses import dataclass


@dataclass
class Sample:
    sample_id: str
    name: str
    avg_production_time: float
    yield_rate: float
    stock: int = 0

    def __post_init__(self):
        if not (0 < self.yield_rate <= 1):
            raise ValueError(f"yield_rate는 0 초과 1 이하여야 합니다: {self.yield_rate}")
