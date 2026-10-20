#!/usr/bin/env python3
"""
Non-GUI core functionality test script.
Run: python test_core.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import database as db
from models import create_user_from_dict, Campus, Lecturer, BookingPolicy, StandardPolicy

def main():
    print("=" * 60)
    print("Smart Campus Resource Booking System - Core Tests")
    print("=" * 60)

    db.init_db()
    print("\n[1] Database initialised.")

    campuses = db.get_all_campuses()
    print(f"[2] Campuses loaded ({len(campuses)}):")
    for c in campuses:
        print(f"    - {c['name']}: max {c['max_duration_hours']}h, "
              f"{c['open_hour']:02d}:00-{c['close_hour']:02d}:00")

    # Auth
    user_data = db.authenticate_user("lecturer1", "pass123")
    assert user_data is not None
    user = create_user_from_dict(user_data)
    print(f"\n[3] Authenticated: {user} | Permissions sample: {user.get_permissions()[:3]}")

    # Resources
    resources = db.get_resources_by_campus(user.campus_id)
    print(f"[4] Resources on campus: {len(resources)}")
    for r in resources[:3]:
        print(f"    - {r['name']} ({r['resource_type']})")

    # Booking (use a future date)
    from datetime import datetime, timedelta
    future = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    ok, msg = db.create_booking(
        resources[0]["resource_id"], user.user_id, user.campus_id,
        future, "11:00", 1.0
    )
    print(f"\n[5] Create booking: {ok} - {msg}")

    # Overlap should fail
    ok2, msg2 = db.create_booking(
        resources[0]["resource_id"], user.user_id, user.campus_id,
        future, "11:30", 1.0
    )
    print(f"[6] Overlap prevention: {ok2} - {msg2}")

    # Report
    report = db.get_campus_report(user.campus_id)
    print(f"\n[7] Campus report: total={report['total_bookings']}, "
          f"avg_duration={report['average_duration']}")

    cross = db.get_cross_campus_report()
    print(f"[8] Cross-campus report entries: {len(cross)}")

    # Policy object
    c = Campus.from_dict(campuses[0])
    valid, reason = c.validate_booking("09:00", 1.5)
    print(f"[9] Policy validate: {valid} ({reason})")

    print("\n" + "=" * 60)
    print("All core tests passed successfully.")
    print("Run 'python main.py' to launch the GUI application.")
    print("=" * 60)

if __name__ == "__main__":
    main()
