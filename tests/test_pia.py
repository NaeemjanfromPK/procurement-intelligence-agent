"""End-to-end tests for PIA with a mocked LLM - fast, offline, deterministic."""
import importlib
import json
from pathlib import Path

import pytest

from pia.config import settings
from pia.graph import build_graph, run_pia

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CSV = PROJECT_ROOT / "data" / "sample_suppliers.csv"

FAKE_REPORT_MD = (
    "## Executive Briefing\n\n"
    "### Risk Overview\n\n"
    "| Supplier | Risk Level |\n|---|---|\n| SUP-001 | MEDIUM |\n\n"
    "## Recommended Actions\n\n"
    "1. **Dual-source Epsilon Textiles** — reduce single-source dependency."
)

FAKE_STRATEGY_JSON = json.dumps({
    "strategies": [
        {
            "title": "Dual-source Epsilon Textiles",
            "suppliers": ["SUP-005"],
            "impact": "Reduces single-source risk exposure by ~40%",
            "timeline": "1-3 months",
        }
    ],
    "monitoring_plan": ["Quarterly risk re-scoring", "KPI dashboard review"],
})


@pytest.fixture()
def fake_llm(monkeypatch):
    """Replace the LLM in every agent module that imported `chat`."""
    calls: list[dict] = []

    def fake_chat(system, user, *, llm=None, json_mode=False):
        calls.append({"json_mode": json_mode, "user": user[:80]})
        return FAKE_STRATEGY_JSON if json_mode else FAKE_REPORT_MD

    patched = []
    for name in ["ingest", "forecast", "risk", "strategy", "report"]:
        mod = importlib.import_module(f"pia.agents.{name}")
        if hasattr(mod, "chat"):
            monkeypatch.setattr(mod, "chat", fake_chat)
            patched.append(name)

    fake_chat.calls = calls
    fake_chat.patched_modules = patched
    return fake_chat


@pytest.fixture()
def isolated_runs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "runs_dir", tmp_path / "runs")
    return tmp_path / "runs"


def test_graph_has_all_five_agents():
    graph = build_graph()
    assert set(graph.get_graph().nodes) >= {
        "ingest", "forecast", "risk", "strategy", "report", "__start__", "__end__"
    }


def test_pipeline_runs_end_to_end(isolated_runs_dir, fake_llm):
    events: list[str] = []
    final = run_pia(
        str(SAMPLE_CSV),
        "Analyze supplier risk",
        run_id="test_e2e",
        on_event=lambda node, update: events.append(node),
    )

    # All 5 agents executed, in dependency order
    assert events == ["ingest", "forecast", "risk", "strategy", "report"]

    # Artifacts written to the run directory
    run_dir = isolated_runs_dir / "test_e2e"
    for artifact in ["clean.csv", "profile.json", "forecast.json", "risk.json"]:
        assert (run_dir / artifact).exists(), f"missing {artifact}"

    # Final state carries results through the graph
    assert "Executive Briefing" in final["report_md"]
    assert final["report_path"]
    assert (run_dir / "report.md").exists()


def test_strategy_agent_consults_llm(fake_llm, isolated_runs_dir):
    run_pia(str(SAMPLE_CSV), "Analyze supplier risk", run_id="test_llm_calls")

    # Exactly one LLM call per run (strategy agent); report renders from its output
    assert len(fake_llm.calls) == 1, f"expected exactly 1 LLM call, got {fake_llm.calls}"
    assert "procurement strategies" in fake_llm.calls[0]["user"]
    assert fake_llm.calls[0]["json_mode"] is False