"""Seeded demo data for tasks.

Re-created by the admin reset endpoint (`POST /admin/tasks/reset`) so the demo
can always return to its original state. These are owned by whichever admin
triggers the reset.
"""

from typing import Any

SEEDED_TASKS: list[dict[str, Any]] = [
    {
        "title": "Set up project repo",
        "description": "Initialize the git repository and CI.",
        "priority": 1,
        "completed": True,
    },
    {
        "title": "Draft API schema",
        "description": "Define the request and response models.",
        "priority": 2,
        "completed": False,
    },
    {
        "title": "Write tests",
        "description": "Cover auth, CRUD, and owner isolation.",
        "priority": 3,
        "completed": False,
    },
]
