from enum import Enum


class OrderStatus(str, Enum):
    WAITING = "WAITING"
    PREPARATION = "PREPARATION"
    READY = "READY"
    DELIVERED = "DELIVERED"
