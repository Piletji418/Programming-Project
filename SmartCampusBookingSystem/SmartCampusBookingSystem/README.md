# Smart Campus Resource Booking System

**Programming 512 Assignment**  
Richfield Graduate Institution

## Overview

A complete Python desktop application that allows lecturers, campus administrators and system operators to manage shared academic resources (labs, rooms, projectors, halls) across multiple campuses.

### Key Technologies
- **Python 3**
- **Tkinter** – Graphical User Interface
- **SQLite** – Persistent data storage
- **Object-Oriented Programming** – Classes, inheritance, encapsulation
- Structured data collections (lists, dictionaries)

---

## Features Implemented

### User Roles (OOP with Inheritance)
| Role | Capabilities |
|------|--------------|
| **Lecturer** | Register, login, select campus, view resources, create bookings, view & cancel own bookings |
| **Campus Administrator** | Manage (add/update/deactivate) resources for their campus, view campus bookings, campus-level reports |
| **System Operator** | Full access, view all bookings, cross-campus comparative reports |

### Campuses & Booking Policies (at least 3 campuses with different rules)
| Campus | Max Duration | Operating Hours |
|--------|--------------|-----------------|
| Johannesburg Campus | 2 hours | 08:00 – 18:00 |
| Cape Town Campus | 4 hours | 07:00 – 20:00 |
| Durban Campus | 3 hours | 08:00 – 17:00 |

Booking rules are applied automatically and are separated from core logic (policy classes / campus objects) so new campuses or rules can be added with minimal code changes.

### Other Requirements Met
- Prevent overlapping bookings for the same resource
- Real-time availability checking via GUI
- Persistent storage of users, campuses, resources and bookings (SQLite)
- Campus selection clearly displayed in the GUI
- Unique resource identifiers + duplicate detection
- Campus-level reports (total bookings, top resources, average duration)
- Cross-campus comparison for System Operators
- Input validation and error handling throughout
- Well-structured, commented code

---

## How to Run

### Requirements
- Python 3.8 or newer
- No external packages required (uses only standard library: `tkinter`, `sqlite3`)

### Steps
1. Unzip the project folder.
2. Open a terminal / command prompt in the project root.
3. Run:
   ```bash
   python main.py
   ```
   or
   ```bash
   python3 main.py
   ```

On first run the SQLite database is created automatically and seeded with sample campuses, resources and demo user accounts.

---

## Demo Accounts

| Username   | Password  | Role              | Campus              |
|------------|-----------|-------------------|---------------------|
| lecturer1  | pass123   | Lecturer          | Johannesburg        |
| lecturer2  | pass123   | Lecturer          | Cape Town           |
| admin_jhb  | admin123  | Campus Admin      | Johannesburg        |
| admin_ct   | admin123  | Campus Admin      | Cape Town           |
| admin_dbn  | admin123  | Campus Admin      | Durban              |
| operator1  | ops123    | System Operator   | All campuses        |

You can also register new Lecturer accounts from the login screen.

---

## Project Structure

```
SmartCampusBookingSystem/
├── main.py                 # Application entry point
├── README.md               # This file
├── src/
│   ├── database.py         # SQLite schema, CRUD, reports, validation
│   ├── models.py           # OOP classes (User hierarchy, Campus, Resource, Booking, Policies)
│   └── gui.py              # Tkinter login + role-based dashboards
└── data/
    └── campus_booking.db   # Created automatically on first run
```

---

## Design Notes

- **Separation of concerns**: Database logic, domain models and GUI are in separate modules.
- **Booking policies** are encapsulated in `Campus` / `BookingPolicy` classes so future expansion (new campuses or rule types) requires only data or a new policy subclass.
- **Role-based access** is enforced both in the GUI (different tabs) and in the data layer (e.g. lecturers can only cancel their own bookings).
- All user input is validated; clear error messages are shown via message boxes.

---

## Author

Student submission for Programming 512 Assignment.
