from abc import ABC, abstractmethod
from pydantic import BaseModel

class StrategyBase(ABC):

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @abstractmethod
    def generate(self, context, max_retries: int, debug: bool) -> BaseModel:
        pass