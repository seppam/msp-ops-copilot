"""Who is the PIC (person in charge) today? A day-by-day rotation over data/roster.json."""

import json
from datetime import date
from pathlib import Path

ROSTER_FILE = Path(__file__).resolve().parents[2] / "data" / "roster.json"


def on_duty(team: str, today: date | None = None) -> str:
    """Name and role of the PIC on duty for a team, e.g. 'Budi (ops PIC)'. Rotates daily through the roster."""
    names = json.loads(ROSTER_FILE.read_text())[team]
    return f"{names[(today or date.today()).toordinal() % len(names)]} ({team} PIC)"
