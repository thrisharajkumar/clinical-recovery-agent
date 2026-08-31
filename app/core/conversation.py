"""
In-memory session store.

Explicitly a prototype limitation: state is lost on server restart and does
not scale beyond a single process. In production this becomes Redis or a
DB-backed store — the interface below (get/append) is written so that swap
doesn't touch calling code.
"""
from typing import Dict, List

_sessions: Dict[str, List[dict]] = {}


def get_history(session_id: str) -> List[dict]:
    return _sessions.setdefault(session_id, [])


def append_turn(session_id: str, role: str, content) -> None:
    _sessions.setdefault(session_id, []).append({"role": role, "content": content})
