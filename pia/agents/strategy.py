"""Strategy agent — generates procurement recommendations using LLM."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..state import PIAState
from ..llm import chat


STRATEGY_SYSTEM = """You are a Chief Procurement Officer writing an executive briefing.
Given supplier forecast and risk data, produce 3-5 concrete, actionable procurement strategies.
Each strategy must include: what to do, which supplier(s) it applies to, expected impact, and timeline.
Write in professional Markdown. Be specific with numbers from the data."""


def strategy_node(state: PIAState) -> dict[str, Any]:
    """Synthesize forecast + risk into actionable strategies."""
    run_dir = Path(state["run_dir"])

    forecast = state.get("forecast_results", {})
    risk = state.get("risk_scores", {})
    user_prompt = state.get("user_prompt", "Analyze supplier risk and recommend actions")

    log: list[str] = ["Strategy: generating recommendations..."]

    # Build context for LLM
    context = {
        "user_request": user_prompt,
        "supplier_count": len(risk),
        "suppliers": [],
    }

    for sid, r in risk.items():
        f = forecast.get(sid, {})
        context["suppliers"].append({
            "id": sid,
            "name": r["supplier_name"],
            "country": r["country"],
            "category": r["category"],
            "risk_level": r["risk_level"],
            "risk_score": r["total_risk_pct"],
            "spend_share": r["spend_share_pct"],
            "predicted_next_delay": f.get("predicted_next_delay", "N/A"),
            "trend": f.get("trend_slope", 0),
        })

    user_msg = f"""Analyze the following supplier data and provide procurement strategies.

{json.dumps(context, indent=2)}

Generate a Markdown report with these sections:
### Executive Summary
### Risk Overview (table of suppliers with risk scores)
### Recommended Actions (numbered, with timelines)
### Monitoring Plan"""

    try:
        response = chat(STRATEGY_SYSTEM, user_msg)
        recommendations = response
        log.append("Strategy generated successfully")
    except Exception as e:
        recommendations = f"Strategy generation failed: {e}"
        log.append(f"Strategy failed: {e}")

    # Save
    out = run_dir / "strategy.md"
    out.write_text(recommendations, encoding="utf-8")

    return {
        "strategy_recommendations": recommendations,
        "log": log,
    }
