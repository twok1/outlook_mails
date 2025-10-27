from abc import ABC, abstractmethod

class OutlookFilter:
    @abstractmethod
    def apply(self):
        pass