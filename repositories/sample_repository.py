from pathlib import Path
from models.sample import Sample
from repositories.json_repository import load, save


class SampleRepository:
    def __init__(self, filepath):
        self._filepath = Path(filepath)

    def find_all(self) -> list[Sample]:
        data = load(self._filepath)
        return [self._to_sample(d) for d in data] if data else []

    def find_by_id(self, sample_id: str) -> Sample | None:
        return next((s for s in self.find_all() if s.sample_id == sample_id), None)

    def save(self, sample: Sample) -> None:
        all_samples = self.find_all()
        updated = [s for s in all_samples if s.sample_id != sample.sample_id]
        updated.append(sample)
        save(self._filepath, [self._to_dict(s) for s in updated])

    def _to_dict(self, s: Sample) -> dict:
        return {
            "sample_id": s.sample_id,
            "name": s.name,
            "avg_production_time": s.avg_production_time,
            "yield_rate": s.yield_rate,
            "stock": s.stock,
        }

    def _to_sample(self, d: dict) -> Sample:
        return Sample(
            sample_id=d["sample_id"],
            name=d["name"],
            avg_production_time=d["avg_production_time"],
            yield_rate=d["yield_rate"],
            stock=d["stock"],
        )
