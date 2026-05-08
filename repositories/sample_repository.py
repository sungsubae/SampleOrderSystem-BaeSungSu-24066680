from models.sample import Sample
from repositories.base_repository import BaseRepository


class SampleRepository(BaseRepository):
    def _id_of(self, entity: Sample) -> str:
        return entity.sample_id

    def _to_dict(self, s: Sample) -> dict:
        return {
            "sample_id": s.sample_id,
            "name": s.name,
            "avg_production_time": s.avg_production_time,
            "yield_rate": s.yield_rate,
            "stock": s.stock,
        }

    def _from_dict(self, d: dict) -> Sample:
        return Sample(
            sample_id=d["sample_id"],
            name=d["name"],
            avg_production_time=d["avg_production_time"],
            yield_rate=d["yield_rate"],
            stock=d["stock"],
        )
