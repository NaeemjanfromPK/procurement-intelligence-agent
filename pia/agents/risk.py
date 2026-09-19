"""Risk scoring agent — evaluates supplier risk across multiple dimensions."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from ..state import PIAState


# Country risk tiers (simplified)
COUNTRY_RISK = {
    "Germany": 1, "USA": 2, "Japan": 2, "UK": 2,
    "India": 3, "China": 3, "Bangladesh": 4, "Pakistan": 4,
}


def risk_node(state: PIAState) -> dict[str, Any]:
    """Score each supplier on risk: concentration, variance, geography, value."""
    run_dir = Path(state["run_dir"])

    df_dict = state["supplier_df"]
    df = pd.DataFrame(data=df_dict["data"], columns=df_dict["columns"], index=df_dict["index"])

    forecast = state.get("forecast_results", {})

    log: list[str] = ["Risk: scoring suppliers..."]

    total_value = df["value_usd"].sum()
    total_orders = len(df)

    risk_scores: dict[str, Any] = {}

    for sid in df["supplier_id"].unique():
        sub = df[df["supplier_id"] == sid]
        name = sub["supplier_name"].iloc[0]
        country = sub["country"].iloc[0] if "country" in sub.columns else "Unknown"
        category = sub["category"].iloc[0] if "category" in sub.columns else "Unknown"

        # Dimension 1: Concentration risk (% of total spend)
        spend_share = sub["value_usd"].sum() / total_value * 100
        concentration_score = min(spend_share / 20, 5)  # 20% = max score 5

        # Dimension 2: Delay variance risk
        lead_times = sub["lead_time_days"].values
        std_lt = lead_times.std() if len(lead_times) > 1 else 0
        variance_score = min(std_lt / 5, 5)  # std 25 days = max score 5

        # Dimension 3: Trend risk (from forecast)
        trend_score = 0
        if sid in forecast:
            slope = forecast[sid].get("trend_slope", 0)
            trend_score = min(abs(slope) / 2, 5)  # slope 10 = max score 5

        # Dimension 4: Country risk
        country_score = COUNTRY_RISK.get(country, 3)

        # Dimension 5: Single-source risk (only supplier in category?)
        category_suppliers = df[df["category"] == category]["supplier_id"].nunique()
        single_source_score = 3 if category_suppliers == 1 else 0

        # Total risk (0-100 scale)
        raw_total = concentration_score + variance_score + trend_score + country_score + single_source_score
        risk_pct = min(int(raw_total / 21 * 100), 100)

        risk_level = "LOW" if risk_pct < 30 else "MEDIUM" if risk_pct < 60 else "HIGH" if risk_pct < 85 else "CRITICAL"

        risk_scores[sid] = {
            "supplier_name": name,
            "country": country,
            "category": category,
            "concentration_score": round(concentration_score, 2),
            "variance_score": round(variance_score, 2),
            "trend_score": round(trend_score, 2),
            "country_score": country_score,
            "single_source_score": single_source_score,
            "total_risk_pct": risk_pct,
            "risk_level": risk_level,
            "spend_share_pct": round(spend_share, 2),
        }

    # Save
    out = run_dir / "risk.json"
    out.write_text(json.dumps(risk_scores, indent=2), encoding="utf-8")

    high_risk = sum(1 for v in risk_scores.values() if v["risk_level"] in ("HIGH", "CRITICAL"))
    log.append(f"Scored {len(risk_scores)} suppliers, {high_risk} high/critical risk")

    return {
        "risk_scores": risk_scores,
        "log": log,
    }
