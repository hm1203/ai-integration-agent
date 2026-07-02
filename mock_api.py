"""
mock_api.py
A mock enterprise "System API" — stands in for a real Workday/PeopleSoft/
Salesforce backend. This is deliberately shaped like the kind of API you'd
build in MuleSoft's API-led connectivity model: narrow, resource-based,
predictable contracts that a Process/Experience layer (or an AI agent) can
call safely.

Run with:
    uvicorn mock_api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from data import EMPLOYEES, STANDARD_WEEKLY_HOURS

app = FastAPI(
    title="Mock Timekeeping System API",
    description="Mock System API simulating an enterprise HR/timekeeping backend.",
    version="1.0.0",
)


class AnomalyFlag(BaseModel):
    employee_id: str
    reason: str


@app.get("/employees")
def list_employees(department: Optional[str] = None, status: Optional[str] = None):
    """List employees, optionally filtered by department or status."""
    results = list(EMPLOYEES.values())
    if department:
        results = [e for e in results if e["department"].lower() == department.lower()]
    if status:
        results = [e for e in results if e["status"] == status]
    # Return a lightweight summary, not full timesheet payloads
    return [
        {
            "employee_id": e["employee_id"],
            "name": e["name"],
            "department": e["department"],
            "status": e["status"],
        }
        for e in results
    ]


@app.get("/employees/{employee_id}")
def get_employee(employee_id: str):
    """Get basic profile + status for a single employee."""
    emp = EMPLOYEES.get(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    return {
        "employee_id": emp["employee_id"],
        "name": emp["name"],
        "department": emp["department"],
        "status": emp["status"],
    }


@app.get("/employees/{employee_id}/timesheet")
def get_timesheet(employee_id: str):
    """Get the current week's timesheet for an employee."""
    emp = EMPLOYEES.get(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    return {
        "employee_id": emp["employee_id"],
        "name": emp["name"],
        "standard_weekly_hours": STANDARD_WEEKLY_HOURS,
        **emp["timesheet"],
    }


@app.post("/timesheet/flag-anomaly")
def flag_anomaly(flag: AnomalyFlag):
    """
    Persist an anomaly flag against an employee's record.
    In a real system this would write to Workday via a Process API;
    here we just store it in memory so the demo is self-contained.
    """
    emp = EMPLOYEES.get(flag.employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {flag.employee_id} not found")
    emp["flags"].append(flag.reason)
    return {
        "employee_id": flag.employee_id,
        "flag_recorded": flag.reason,
        "total_flags": len(emp["flags"]),
    }


@app.get("/health")
def health():
    return {"status": "ok", "employee_count": len(EMPLOYEES)}
