"""
Object-oriented models for the Smart Campus Resource Booking System.
Demonstrates classes, inheritance, and encapsulation.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime


class User(ABC):
    """Base user class with common attributes and authentication."""

    def __init__(self, user_id: int, username: str, full_name: str, role: str,
                 campus_id: Optional[int] = None):
        self._user_id = user_id
        self._username = username
        self._full_name = full_name
        self._role = role
        self._campus_id = campus_id

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def full_name(self) -> str:
        return self._full_name

    @property
    def role(self) -> str:
        return self._role

    @property
    def campus_id(self) -> Optional[int]:
        return self._campus_id

    def __str__(self) -> str:
        return f"{self._full_name} ({self._role})"

    @abstractmethod
    def get_permissions(self) -> List[str]:
        """Return list of permissions for this role."""
        pass


class Lecturer(User):
    """Lecturer role: can book resources and manage own bookings."""

    def __init__(self, user_id: int, username: str, full_name: str, campus_id: Optional[int] = None):
        super().__init__(user_id, username, full_name, "lecturer", campus_id)

    def get_permissions(self) -> List[str]:
        return [
            "view_own_bookings",
            "create_booking",
            "cancel_own_booking",
            "view_resources",
            "select_campus",
        ]


class CampusAdministrator(User):
    """Campus Administrator: manages resources and views bookings for one campus."""

    def __init__(self, user_id: int, username: str, full_name: str, campus_id: int):
        super().__init__(user_id, username, full_name, "admin", campus_id)

    def get_permissions(self) -> List[str]:
        return [
            "manage_resources",
            "view_campus_bookings",
            "view_resources",
            "view_reports_campus",
            "select_campus",  # restricted to own campus usually
        ]


class SystemOperator(User):
    """System Operator: full institutional access and cross-campus reports."""

    def __init__(self, user_id: int, username: str, full_name: str):
        super().__init__(user_id, username, full_name, "operator", None)

    def get_permissions(self) -> List[str]:
        return [
            "view_all_bookings",
            "view_all_resources",
            "view_cross_campus_reports",
            "select_any_campus",
            "view_reports_campus",
        ]


def create_user_from_dict(data: Dict) -> User:
    """Factory function to instantiate the correct User subclass."""
    role = data.get("role", "").lower()
    uid = data["user_id"]
    uname = data["username"]
    fname = data["full_name"]
    cid = data.get("campus_id")

    if role == "lecturer":
        return Lecturer(uid, uname, fname, cid)
    elif role == "admin":
        return CampusAdministrator(uid, uname, fname, cid)
    elif role == "operator":
        return SystemOperator(uid, uname, fname)
    else:
        raise ValueError(f"Unknown role: {role}")


class Campus:
    """Represents a campus with its booking policy encapsulated."""

    def __init__(self, campus_id: int, name: str, location: str,
                 max_duration_hours: float, open_hour: int, close_hour: int,
                 description: str = ""):
        self._campus_id = campus_id
        self._name = name
        self._location = location
        self._max_duration_hours = max_duration_hours
        self._open_hour = open_hour
        self._close_hour = close_hour
        self._description = description

    @property
    def campus_id(self) -> int:
        return self._campus_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def max_duration_hours(self) -> float:
        return self._max_duration_hours

    @property
    def open_hour(self) -> int:
        return self._open_hour

    @property
    def close_hour(self) -> int:
        return self._close_hour

    @property
    def policy_description(self) -> str:
        return (f"Max duration: {self._max_duration_hours}h | "
                f"Hours: {self._open_hour:02d}:00 - {self._close_hour:02d}:00")

    def validate_booking(self, start_time: str, duration_hours: float) -> tuple[bool, str]:
        """Validate a proposed booking against this campus's rules."""
        if duration_hours <= 0 or duration_hours > self._max_duration_hours:
            return False, f"Duration must be > 0 and ≤ {self._max_duration_hours} hours."
        try:
            h, m = map(int, start_time.split(":"))
            end_min = h * 60 + m + int(duration_hours * 60)
            end_h = end_min // 60
            if h < self._open_hour or end_h > self._close_hour or \
               (end_h == self._close_hour and end_min % 60 > 0):
                return False, (f"Must be within {self._open_hour:02d}:00-"
                               f"{self._close_hour:02d}:00.")
        except ValueError:
            return False, "Invalid time format."
        return True, "OK"

    @classmethod
    def from_dict(cls, data: Dict) -> "Campus":
        return cls(
            data["campus_id"], data["name"], data.get("location", ""),
            data["max_duration_hours"], data["open_hour"], data["close_hour"],
            data.get("description", "")
        )


class Resource:
    """Campus resource (lab, room, equipment)."""

    def __init__(self, resource_id: int, campus_id: int, name: str,
                 resource_type: str, capacity: int = 1, description: str = "",
                 is_active: bool = True):
        self._resource_id = resource_id
        self._campus_id = campus_id
        self._name = name
        self._resource_type = resource_type
        self._capacity = capacity
        self._description = description
        self._is_active = is_active

    @property
    def resource_id(self) -> int:
        return self._resource_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def resource_type(self) -> str:
        return self._resource_type

    @property
    def is_active(self) -> bool:
        return self._is_active

    def __str__(self) -> str:
        return f"{self._name} ({self._resource_type})"

    @classmethod
    def from_dict(cls, data: Dict) -> "Resource":
        return cls(
            data["resource_id"], data["campus_id"], data["name"],
            data["resource_type"], data.get("capacity", 1),
            data.get("description", ""), bool(data.get("is_active", 1))
        )


class Booking:
    """A resource booking record."""

    def __init__(self, booking_id: int, resource_id: int, user_id: int,
                 campus_id: int, booking_date: str, start_time: str,
                 duration_hours: float, end_time: str, status: str = "active"):
        self._booking_id = booking_id
        self._resource_id = resource_id
        self._user_id = user_id
        self._campus_id = campus_id
        self._booking_date = booking_date
        self._start_time = start_time
        self._duration_hours = duration_hours
        self._end_time = end_time
        self._status = status

    @property
    def booking_id(self) -> int:
        return self._booking_id

    @property
    def status(self) -> str:
        return self._status

    def is_future(self) -> bool:
        try:
            d = datetime.strptime(self._booking_date, "%Y-%m-%d").date()
            return d >= datetime.now().date()
        except ValueError:
            return False

    @classmethod
    def from_dict(cls, data: Dict) -> "Booking":
        return cls(
            data["booking_id"], data["resource_id"], data["user_id"],
            data["campus_id"], data["booking_date"], data["start_time"],
            data["duration_hours"], data["end_time"], data.get("status", "active")
        )


# -------------------- Booking Policy Strategy (for future expansion) --------------------

class BookingPolicy(ABC):
    """Abstract base for campus-specific booking policies.
    Separates rules from core logic so new policies can be added easily.
    """

    @abstractmethod
    def max_duration(self) -> float:
        pass

    @abstractmethod
    def operating_hours(self) -> tuple[int, int]:
        pass

    @abstractmethod
    def validate(self, start_time: str, duration: float) -> tuple[bool, str]:
        pass

    @abstractmethod
    def description(self) -> str:
        pass


class StandardPolicy(BookingPolicy):
    """Concrete policy driven by campus data."""

    def __init__(self, max_dur: float, open_h: int, close_h: int, name: str = ""):
        self._max_dur = max_dur
        self._open = open_h
        self._close = close_h
        self._name = name

    def max_duration(self) -> float:
        return self._max_dur

    def operating_hours(self) -> tuple[int, int]:
        return self._open, self._close

    def validate(self, start_time: str, duration: float) -> tuple[bool, str]:
        if duration <= 0 or duration > self._max_dur:
            return False, f"Duration must be ≤ {self._max_dur}h"
        try:
            h, m = map(int, start_time.split(":"))
            end = h * 60 + m + int(duration * 60)
            if h < self._open or (end // 60) > self._close:
                return False, f"Outside {self._open:02d}:00-{self._close:02d}:00"
        except Exception:
            return False, "Invalid time"
        return True, "OK"

    def description(self) -> str:
        return (f"{self._name}: Max {self._max_dur}h, "
                f"{self._open:02d}:00-{self._close:02d}:00")
