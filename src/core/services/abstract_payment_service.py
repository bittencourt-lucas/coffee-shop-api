from abc import ABC, abstractmethod
from decimal import Decimal


class AbstractPaymentService(ABC):
    @abstractmethod
    async def process(self, value: Decimal) -> dict:
        ...
