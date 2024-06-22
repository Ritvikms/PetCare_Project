from enum import Enum


# enums
class ServiceProviderStatus(Enum):
    PENDING = 1
    APPROVED = 2
    REJECTED = 3
    DELETED = 4


class AppointmentStatus(Enum):
    PENDING = 1
    SCHEDULED = 2
    CANCELLED = 3
    REJECTED = 4
