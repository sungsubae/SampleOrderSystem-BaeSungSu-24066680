from models.sample import Sample
from repositories.sample_repository import SampleRepository


class SampleController:
    def __init__(self, repository: SampleRepository):
        self._repo = repository

    def register(self, sample_id: str, name: str, avg_time: float, yield_rate: float) -> Sample:
        if self._repo.find_by_id(sample_id) is not None:
            raise ValueError(f"이미 등록된 시료 ID입니다: {sample_id}")
        sample = Sample(
            sample_id=sample_id,
            name=name,
            avg_production_time=avg_time,
            yield_rate=yield_rate,
        )
        self._repo.save(sample)
        return sample

    def list_all(self) -> list[Sample]:
        return self._repo.find_all()

    def search(self, keyword: str) -> list[Sample]:
        keyword_lower = keyword.lower()
        return [s for s in self._repo.find_all() if keyword_lower in s.name.lower()]
