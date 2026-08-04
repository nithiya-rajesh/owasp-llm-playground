"""
Simple in-memory session store. Fine for a local single-user training app.
NOT suitable for multi-user production use (no persistence, no isolation
guarantees beyond the dict key, no expiry).
"""

import uuid
from dataclasses import dataclass, field


@dataclass
class SessionData:
    conversation: list = field(default_factory=list)
    scenario_state: dict = field(default_factory=dict)  # scoped per scenario_id
    captured_flags: set = field(default_factory=set)


_SESSIONS: dict[str, SessionData] = {}


def new_session_id() -> str:
    return uuid.uuid4().hex[:12]


def get_session(session_id: str) -> SessionData:
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = SessionData()
    return _SESSIONS[session_id]


def reset_scenario(session_id: str, scenario_id: str):
    session = get_session(session_id)
    session.conversation = []
    session.scenario_state[scenario_id] = {}


def get_scenario_state(session_id: str, scenario_id: str) -> dict:
    session = get_session(session_id)
    return session.scenario_state.setdefault(scenario_id, {})
