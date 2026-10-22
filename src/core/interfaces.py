from abc import ABC, abstractmethod
from typing import List, Any

from src.models import EmailData

class BaseMailParser(ABC):
    @abstractmethod
    def run(self, items: List[EmailData]) -> List[Any]:
        """Принимает сырые письма, возвращаем распарсеные"""
        pass
  
  
class BaseMailProcessor(ABC):
    @abstractmethod
    def process(self, items: List[Any]) -> None:
        """выполняет операции с парсеными письмами"""
        pass