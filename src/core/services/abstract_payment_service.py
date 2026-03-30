from abc import ABC, abstractmethod


class AbstractPaymentService(ABC):
    @abstractmethod
    async def process(self, value: float) -> dict:
        ...
