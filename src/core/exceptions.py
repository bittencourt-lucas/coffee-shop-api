class PaymentFailedError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class InvalidStatusTransitionError(Exception):
    def __init__(self, current: str, new: str) -> None:
        super().__init__(f"Cannot transition from {current} to {new}")
