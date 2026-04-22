class PaymentFailedError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class InvalidStatusTransitionError(Exception):
    def __init__(self, current: str, new: str) -> None:
        super().__init__(f"Cannot transition from {current} to {new}")


class InvalidProductError(Exception):
    def __init__(self, missing_ids: list) -> None:
        formatted = ", ".join(str(pid) for pid in missing_ids)
        super().__init__(f"Products not found: {formatted}")


class InvalidCredentialsError(Exception):
    pass


class DuplicateEmailError(Exception):
    pass
