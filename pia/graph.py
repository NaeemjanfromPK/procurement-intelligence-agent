"""LangGraph workflow for Procurement Intelligence Agent."""
from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from langgraph.graph import END, START, StateGraph

from .agents.forecast import forecast_node
from .agents.ingest import ingest_node
from .agents.report import report_node
from .agents.risk import risk_node
from .agents.strategy import strategy_node
from .config import settings
from .state import PIAState, new_state


def build_graph():
    builder = StateGraph(PIAState)

    builder.add_node("ingest", ingest_node)
    builder.add_node("forecast", forecast_node)
    builder.add_node("risk", risk_node)
    builder.add_node("strategy", strategy_node)
    builder.add_node("report", report_node)

    # Sequential flow: ingest -> (forecast + risk in parallel) -> strategy -> report
    builder.add_edge(START, "ingest")
    builder.add_edge("ingest", "forecast")
    builder.add_edge("ingest", "risk")
    builder.add_edge("forecast", "strategy")
    builder.add_edge("risk", "strategy")
    builder.add_edge("strategy", "report")
    builder.add_edge("report", END)

    return builder.compile()


def make_run_dir(run_id: str) -> Path:
    path = settings.runs_dir / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_pia(data_path: str, user_prompt: str, *, run_id: str | None = None,
            on_event=None) -> PIAState:
    run_id = run_id or f"{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}"
    run_dir = make_run_dir(run_id)

    graph = build_graph()
    initial = new_state(str(data_path), user_prompt, run_id, str(run_dir))

    final: PIAState = dict(initial)
    for mode, chunk in graph.stream(
        initial,
        stream_mode=["updates", "values"],
    ):
        if mode == "updates":
            for node_name, update in (chunk or {}).items():
                if on_event and isinstance(update, dict):
                    on_event(node_name, update)
        elif mode == "values" and isinstance(chunk, dict):
            final = chunk

    return final
