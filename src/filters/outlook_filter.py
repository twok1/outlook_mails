from abc import ABC, abstractmethod

class OutlookFilter(ABC):
    @abstractmethod
    def apply(self):
        pass