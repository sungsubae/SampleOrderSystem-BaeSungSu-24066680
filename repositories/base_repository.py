from abc import ABC, abstractmethod
from pathlib import Path
from repositories.json_repository import load
from repositories.json_repository import save as json_save


class BaseRepository(ABC):
    def __init__(self, filepath):
        self._filepath = Path(filepath)

    def find_all(self) -> list:
        return [self._from_dict(d) for d in load(self._filepath)]

    def find_by_id(self, entity_id: str):
        return next((e for e in self.find_all() if self._id_of(e) == entity_id), None)

    def save(self, entity) -> None:
        all_entities = self.find_all()
        updated = [e for e in all_entities if self._id_of(e) != self._id_of(entity)]
        updated.append(entity)
        json_save(self._filepath, [self._to_dict(e) for e in updated])

    @abstractmethod
    def _id_of(self, entity) -> str: ...

    @abstractmethod
    def _to_dict(self, entity) -> dict: ...

    @abstractmethod
    def _from_dict(self, d: dict): ...
