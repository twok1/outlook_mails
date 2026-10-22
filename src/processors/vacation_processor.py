from typing import Any, List

from src.core.interfaces import BaseMailProcessor
from src.integrations.filesystem import VacationStorage
from src.models import VacationData
from src.utils import Config

class VacationProcessor(BaseMailProcessor):
    def __init__(self, vacation_storage: VacationStorage) -> None:
        self.storage = vacation_storage
    
    def process(self, items: List[VacationData]) -> None:
        self.storage.save_vacations(vacations=items)