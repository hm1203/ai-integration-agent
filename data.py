"""
data.py
Generates deterministic mock enterprise data: employees + weekly timesheets.
Stands in for what a real System API (Workday/PeopleSoft-style) would return.
"""

import random

random.seed(42)  # deterministic so demo output is reproducible

FIRST_NAMES = [
    "James", "Maria", "Wei", "Fatima", "Liam", "Priya", "Noah", "Aisha",
    "Carlos", "Yuki", "Emma", "Raj", "Sofia", "Ahmed", "Olivia", "Ken",
    "Grace", "Diego", "Anya", "Sam"
]
LAST_NAMES = [
    "Chen", "Garcia", "Patel", "Kim", "Smith", "Nguyen", "Khan", "Silva",
    "Johnson", "Mehta", "Rossi", "Muller", "Kowalski", "Tanaka", "Brown"
]
DEPARTMENTS = ["Engineering", "Finance", "Operations", "HR", "Sales", "IT Support"]

STANDARD_WEEKLY_HOURS = 40.0


def _generate_employees(n=50):
    employees = {}
    for i in range(1, n + 1):
        emp_id = f"E{1000 + i}"
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        dept = random.choice(DEPARTMENTS)

        # Most employees have normal hours; ~15% have an overtime spike
        # to simulate real anomalies an integration/AI layer should catch.
        is_anomaly = random.random() < 0.15
        if is_anomaly:
            regular_hours = round(random.uniform(38, 40), 1)
            overtime_hours = round(random.uniform(12, 25), 1)  # spike
        else:
            regular_hours = round(random.uniform(35, 40), 1)
            overtime_hours = round(random.uniform(0, 4), 1)

        employees[emp_id] = {
            "employee_id": emp_id,
            "name": f"{first} {last}",
            "department": dept,
            "status": random.choice(["active", "active", "active", "on_leave"]),
            "timesheet": {
                "week_ending": "2026-06-28",
                "regular_hours": regular_hours,
                "overtime_hours": overtime_hours,
                "total_hours": round(regular_hours + overtime_hours, 1),
            },
            "flags": [],
        }
    return employees


EMPLOYEES = _generate_employees()
