import os
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.scenarios import all_scenarios, get_scenario
from app.core import state as state_store
from app.core.agent import run_agent_turn
from app.core.config import describe_active_provider

app = FastAPI(title="OWASP LLM Top 10 Playground")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/scenarios")
def list_scenarios():
    return [
        {
            "id": s.id,
            "owasp_id": s.owasp_id,
            "title": s.title,
            "difficulty": s.difficulty,
            "tagline": s.tagline,
            "objective_md": s.objective_md,
            "hints_md": s.hints_md,
            "fix_md": s.fix_md,
        }
        for s in all_scenarios()
    ]


class ChatRequest(BaseModel):
    session_id: str | None = None
    scenario_id: str
    message: str


@app.post("/api/chat")
def chat(req: ChatRequest):
    scenario = get_scenario(req.scenario_id)
    if scenario is None:
        return JSONResponse({"error": "unknown scenario"}, status_code=404)

    session_id = req.session_id or state_store.new_session_id()
    session = state_store.get_session(session_id)
    scen_state = state_store.get_scenario_state(session_id, req.scenario_id)

    session.conversation.append({"role": "user", "content": req.message})

    try:
        tool_impl = scenario.tool_impl_factory(scen_state)
        result = run_agent_turn(
            system_prompt=scenario.system_prompt,
            tools=scenario.tools,
            tool_impl=tool_impl,
            conversation=session.conversation,
        )
    except Exception as e:  # noqa: BLE001
        # Last-resort safety net: guarantees the frontend always gets JSON
        # back, never a bare framework error page, even if a provider or
        # scenario bug slips past its own error handling.
        return JSONResponse(
            {
                "session_id": session_id,
                "reply": f"[Unexpected server error: {e}. Check the server logs for the full traceback.]",
                "tool_calls": [],
                "flag": None,
                "hit_turn_limit": False,
            }
        )

    session.conversation = result.raw_messages

    flag = scenario.check_flag(scen_state, result.tool_calls, result.reply)
    newly_captured = False
    if flag and flag not in session.captured_flags:
        session.captured_flags.add(flag)
        newly_captured = True

    return {
        "session_id": session_id,
        "reply": result.reply,
        "tool_calls": [
            {"name": tc.name, "input": tc.input, "output": tc.output} for tc in result.tool_calls
        ],
        "flag": flag if newly_captured else None,
        "hit_turn_limit": result.hit_turn_limit,
    }


class ResetRequest(BaseModel):
    session_id: str
    scenario_id: str


@app.post("/api/reset")
def reset(req: ResetRequest):
    state_store.reset_scenario(req.session_id, req.scenario_id)
    return {"ok": True}


@app.get("/api/provider")
def provider_info():
    return {"description": describe_active_provider()}


@app.get("/api/health")
def health():
    return {"status": "ok"}
