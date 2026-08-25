"""Seeded demo data for checklists (mission checklist items).

Re-created by the admin reset endpoint (`POST /admin/checklists/reset`) so the demo
can always return to its original state. These are owned by whichever admin
triggers the reset.
"""

from typing import Any

SEEDED_CHECKLISTS: list[dict[str, Any]] = [
    {
        "checklist_item": "Verify oxygen levels",
        "description": "Confirm life support is nominal before launch.",
        "criticality": 1,
        "executed": True,
        "mission_id": 1,
        "notes": "Pre-launch safety check.",
    },
    {
        "checklist_item": "Calibrate navigation",
        "description": "Align the star tracker and inertial units.",
        "criticality": 2,
        "executed": False,
        "mission_id": 1,
        "notes": None,
    },
    {
        "checklist_item": "Deploy solar array",
        "description": "Extend panels and verify power output.",
        "criticality": 3,
        "executed": False,
        "mission_id": 2,
        "notes": None,
    },
]
