"""
Database module for Smart Campus Resource Booking System.
Handles SQLite connection, schema creation, and data operations.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "campus_booking.db")


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create tables if they do not exist and seed initial data."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('lecturer', 'admin', 'operator')),
            campus_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campus_id) REFERENCES campuses(campus_id)
        )
    """)

    # Campuses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campuses (
            campus_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            location TEXT,
            max_duration_hours REAL NOT NULL,
            open_hour INTEGER NOT NULL,
            close_hour INTEGER NOT NULL,
            description TEXT
        )
    """)

    # Resources table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
            campus_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            capacity INTEGER DEFAULT 1,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            UNIQUE(campus_id, name),
            FOREIGN KEY (campus_id) REFERENCES campuses(campus_id)
        )
    """)

    # Bookings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            campus_id INTEGER NOT NULL,
            booking_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            duration_hours REAL NOT NULL,
            end_time TEXT NOT NULL,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'cancelled', 'completed')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resource_id) REFERENCES resources(resource_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (campus_id) REFERENCES campuses(campus_id)
        )
    """)

    conn.commit()

    # Seed campuses if empty
    cursor.execute("SELECT COUNT(*) FROM campuses")
    if cursor.fetchone()[0] == 0:
        campuses = [
            ("Johannesburg Campus", "Johannesburg, Gauteng", 2.0, 8, 18,
             "Max 2 hours per booking. Operating hours 08:00-18:00."),
            ("Cape Town Campus", "Cape Town, Western Cape", 4.0, 7, 20,
             "Max 4 hours per booking. Operating hours 07:00-20:00."),
            ("Durban Campus", "Durban, KwaZulu-Natal", 3.0, 8, 17,
             "Max 3 hours per booking. Operating hours 08:00-17:00. Priority for academic staff."),
        ]
        cursor.executemany(
            "INSERT INTO campuses (name, location, max_duration_hours, open_hour, close_hour, description) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            campuses
        )
        conn.commit()

    # Seed default users if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Get campus IDs
        cursor.execute("SELECT campus_id, name FROM campuses")
        campus_map = {row["name"]: row["campus_id"] for row in cursor.fetchall()}

        users = [
            ("lecturer1", "pass123", "Dr. Thabo Molefe", "lecturer", campus_map.get("Johannesburg Campus")),
            ("lecturer2", "pass123", "Prof. Aisha Naidoo", "lecturer", campus_map.get("Cape Town Campus")),
            ("admin_jhb", "admin123", "Admin Johannesburg", "admin", campus_map.get("Johannesburg Campus")),
            ("admin_ct", "admin123", "Admin Cape Town", "admin", campus_map.get("Cape Town Campus")),
            ("admin_dbn", "admin123", "Admin Durban", "admin", campus_map.get("Durban Campus")),
            ("operator1", "ops123", "System Operator", "operator", None),
        ]
        cursor.executemany(
            "INSERT INTO users (username, password, full_name, role, campus_id) VALUES (?, ?, ?, ?, ?)",
            users
        )
        conn.commit()

    # Seed sample resources if empty
    cursor.execute("SELECT COUNT(*) FROM resources")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT campus_id, name FROM campuses")
        campuses = cursor.fetchall()
        for camp in campuses:
            cid = camp["campus_id"]
            resources = [
                (cid, "Computer Lab A", "Lab", 30, "General purpose computer laboratory"),
                (cid, "Computer Lab B", "Lab", 25, "Programming and networking lab"),
                (cid, "Seminar Room 1", "Room", 20, "Small seminar / meeting room"),
                (cid, "Multimedia Projector 1", "Equipment", 1, "Portable HD projector"),
                (cid, "Lecture Hall 101", "Hall", 80, "Main lecture hall with AV"),
            ]
            cursor.executemany(
                "INSERT INTO resources (campus_id, name, resource_type, capacity, description) "
                "VALUES (?, ?, ?, ?, ?)",
                resources
            )
        conn.commit()

    conn.close()


# -------------------- User Operations --------------------

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user and return user dict or None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, password)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def register_lecturer(username: str, password: str, full_name: str, campus_id: int) -> Tuple[bool, str]:
    """Register a new lecturer account."""
    if not username or not password or not full_name:
        return False, "All fields are required."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, full_name, role, campus_id) VALUES (?, ?, ?, 'lecturer', ?)",
            (username, password, full_name, campus_id)
        )
        conn.commit()
        return True, "Registration successful. You can now log in."
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    finally:
        conn.close()


def get_all_campuses() -> List[Dict]:
    """Return list of all campuses."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campuses ORDER BY name")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_campus_by_id(campus_id: int) -> Optional[Dict]:
    """Return campus by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campuses WHERE campus_id = ?", (campus_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# -------------------- Resource Operations --------------------

def get_resources_by_campus(campus_id: int, active_only: bool = True) -> List[Dict]:
    """Return resources for a campus."""
    conn = get_connection()
    cursor = conn.cursor()
    if active_only:
        cursor.execute(
            "SELECT * FROM resources WHERE campus_id = ? AND is_active = 1 ORDER BY name",
            (campus_id,)
        )
    else:
        cursor.execute(
            "SELECT * FROM resources WHERE campus_id = ? ORDER BY name",
            (campus_id,)
        )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def add_resource(campus_id: int, name: str, resource_type: str, capacity: int, description: str) -> Tuple[bool, str]:
    """Add a new resource. Returns (success, message)."""
    if not name or not resource_type:
        return False, "Name and type are required."
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO resources (campus_id, name, resource_type, capacity, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (campus_id, name.strip(), resource_type.strip(), capacity, description)
        )
        conn.commit()
        return True, "Resource added successfully."
    except sqlite3.IntegrityError:
        return False, "A resource with this name already exists on this campus."
    finally:
        conn.close()


def update_resource(resource_id: int, name: str, resource_type: str, capacity: int,
                    description: str, is_active: int) -> Tuple[bool, str]:
    """Update an existing resource."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE resources SET name=?, resource_type=?, capacity=?, description=?, is_active=? "
            "WHERE resource_id=?",
            (name.strip(), resource_type.strip(), capacity, description, is_active, resource_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return False, "Resource not found."
        return True, "Resource updated successfully."
    except sqlite3.IntegrityError:
        return False, "Duplicate resource name on this campus."
    finally:
        conn.close()


def delete_resource(resource_id: int) -> Tuple[bool, str]:
    """Soft-delete (deactivate) a resource."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE resources SET is_active = 0 WHERE resource_id = ?", (resource_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return (True, "Resource deactivated.") if success else (False, "Resource not found.")


# -------------------- Booking Operations --------------------

def _time_to_minutes(t: str) -> int:
    """Convert HH:MM to minutes since midnight."""
    h, m = map(int, t.split(":"))
    return h * 60 + m


def check_overlap(resource_id: int, booking_date: str, start_time: str, end_time: str,
                  exclude_booking_id: Optional[int] = None) -> bool:
    """Return True if there is an overlapping active booking."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT booking_id, start_time, end_time FROM bookings
        WHERE resource_id = ? AND booking_date = ? AND status = 'active'
    """
    params: List[Any] = [resource_id, booking_date]
    if exclude_booking_id:
        query += " AND booking_id != ?"
        params.append(exclude_booking_id)
    cursor.execute(query, params)
    new_start = _time_to_minutes(start_time)
    new_end = _time_to_minutes(end_time)
    for row in cursor.fetchall():
        existing_start = _time_to_minutes(row["start_time"])
        existing_end = _time_to_minutes(row["end_time"])
        if new_start < existing_end and new_end > existing_start:
            conn.close()
            return True
    conn.close()
    return False


def create_booking(resource_id: int, user_id: int, campus_id: int, booking_date: str,
                   start_time: str, duration_hours: float) -> Tuple[bool, str]:
    """Create a new booking after validation."""
    # Validate duration and hours against campus policy
    campus = get_campus_by_id(campus_id)
    if not campus:
        return False, "Invalid campus."

    if duration_hours <= 0 or duration_hours > campus["max_duration_hours"]:
        return False, f"Duration must be between 0.5 and {campus['max_duration_hours']} hours for this campus."

    try:
        start_h, start_m = map(int, start_time.split(":"))
    except ValueError:
        return False, "Invalid start time format. Use HH:MM."

    end_minutes = start_h * 60 + start_m + int(duration_hours * 60)
    end_h = end_minutes // 60
    end_m = end_minutes % 60
    end_time = f"{end_h:02d}:{end_m:02d}"

    if start_h < campus["open_hour"] or end_h > campus["close_hour"] or \
       (end_h == campus["close_hour"] and end_m > 0):
        return False, (f"Booking must be within campus hours "
                       f"{campus['open_hour']:02d}:00 - {campus['close_hour']:02d}:00.")

    # Check date is not in the past
    try:
        bdate = datetime.strptime(booking_date, "%Y-%m-%d").date()
        if bdate < datetime.now().date():
            return False, "Cannot book a date in the past."
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD."

    if check_overlap(resource_id, booking_date, start_time, end_time):
        return False, "This resource is already booked for the selected time slot."

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO bookings
               (resource_id, user_id, campus_id, booking_date, start_time, duration_hours, end_time, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'active')""",
            (resource_id, user_id, campus_id, booking_date, start_time, duration_hours, end_time)
        )
        conn.commit()
        return True, "Booking created successfully."
    except Exception as e:
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()


def get_user_bookings(user_id: int, include_cancelled: bool = False) -> List[Dict]:
    """Return bookings for a user with resource and campus names."""
    conn = get_connection()
    cursor = conn.cursor()
    status_filter = "" if include_cancelled else "AND b.status = 'active'"
    cursor.execute(f"""
        SELECT b.*, r.name AS resource_name, c.name AS campus_name, u.full_name AS user_name
        FROM bookings b
        JOIN resources r ON b.resource_id = r.resource_id
        JOIN campuses c ON b.campus_id = c.campus_id
        JOIN users u ON b.user_id = u.user_id
        WHERE b.user_id = ? {status_filter}
        ORDER BY b.booking_date DESC, b.start_time DESC
    """, (user_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_campus_bookings(campus_id: int, status: str = "active") -> List[Dict]:
    """Return all bookings for a campus."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, r.name AS resource_name, u.full_name AS user_name, u.username
        FROM bookings b
        JOIN resources r ON b.resource_id = r.resource_id
        JOIN users u ON b.user_id = u.user_id
        WHERE b.campus_id = ? AND b.status = ?
        ORDER BY b.booking_date DESC, b.start_time DESC
    """, (campus_id, status))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_all_bookings() -> List[Dict]:
    """Return all bookings across campuses (for operator)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, r.name AS resource_name, c.name AS campus_name, u.full_name AS user_name
        FROM bookings b
        JOIN resources r ON b.resource_id = r.resource_id
        JOIN campuses c ON b.campus_id = c.campus_id
        JOIN users u ON b.user_id = u.user_id
        ORDER BY b.booking_date DESC, b.start_time DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def cancel_booking(booking_id: int, user_id: int, is_admin: bool = False) -> Tuple[bool, str]:
    """Cancel a booking. Lecturers can only cancel their own future bookings."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "Booking not found."
    booking = dict(row)
    if booking["status"] != "active":
        conn.close()
        return False, "Booking is not active."
    if not is_admin and booking["user_id"] != user_id:
        conn.close()
        return False, "You can only cancel your own bookings."
    # Check if future
    try:
        bdate = datetime.strptime(booking["booking_date"], "%Y-%m-%d").date()
        if bdate < datetime.now().date():
            conn.close()
            return False, "Cannot cancel past bookings."
    except ValueError:
        pass
    cursor.execute("UPDATE bookings SET status = 'cancelled' WHERE booking_id = ?", (booking_id,))
    conn.commit()
    conn.close()
    return True, "Booking cancelled successfully."


def is_resource_available(resource_id: int, booking_date: str, start_time: str, duration_hours: float) -> bool:
    """Check availability for a proposed slot."""
    try:
        start_h, start_m = map(int, start_time.split(":"))
        end_minutes = start_h * 60 + start_m + int(duration_hours * 60)
        end_time = f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"
    except Exception:
        return False
    return not check_overlap(resource_id, booking_date, start_time, end_time)


# -------------------- Reporting --------------------

def get_campus_report(campus_id: int) -> Dict[str, Any]:
    """Generate campus-level report."""
    conn = get_connection()
    cursor = conn.cursor()

    # Total bookings (all statuses for history, or active+completed)
    cursor.execute(
        "SELECT COUNT(*) FROM bookings WHERE campus_id = ? AND status != 'cancelled'",
        (campus_id,)
    )
    total_bookings = cursor.fetchone()[0]

    # Most frequently used resources
    cursor.execute("""
        SELECT r.name, COUNT(*) as cnt
        FROM bookings b
        JOIN resources r ON b.resource_id = r.resource_id
        WHERE b.campus_id = ? AND b.status != 'cancelled'
        GROUP BY r.resource_id
        ORDER BY cnt DESC
        LIMIT 5
    """, (campus_id,))
    top_resources = [(row[0], row[1]) for row in cursor.fetchall()]

    # Average duration
    cursor.execute(
        "SELECT AVG(duration_hours) FROM bookings WHERE campus_id = ? AND status != 'cancelled'",
        (campus_id,)
    )
    avg_duration = cursor.fetchone()[0] or 0.0

    # Active bookings count
    cursor.execute(
        "SELECT COUNT(*) FROM bookings WHERE campus_id = ? AND status = 'active'",
        (campus_id,)
    )
    active_count = cursor.fetchone()[0]

    conn.close()
    return {
        "total_bookings": total_bookings,
        "active_bookings": active_count,
        "top_resources": top_resources,
        "average_duration": round(avg_duration, 2),
    }


def get_cross_campus_report() -> List[Dict]:
    """Comparative report across all campuses."""
    campuses = get_all_campuses()
    report = []
    for c in campuses:
        r = get_campus_report(c["campus_id"])
        r["campus_name"] = c["name"]
        r["campus_id"] = c["campus_id"]
        r["max_duration"] = c["max_duration_hours"]
        r["hours"] = f"{c['open_hour']:02d}:00-{c['close_hour']:02d}:00"
        report.append(r)
    return report


if __name__ == "__main__":
    init_db()
    print("Database initialised successfully at:", DB_PATH)
