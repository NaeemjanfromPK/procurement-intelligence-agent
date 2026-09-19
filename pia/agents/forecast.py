"""Forecast agent — predicts delivery delays per supplier using time-series trends."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..state import PIAState


def forecast_node(state: PIAState) -> dict[str, Any]:
    """Predict next delivery delay and trend per supplier."""
    run_dir = Path(state["run_dir"])

    # Reconstruct DataFrame
    df_dict = state["supplier_df"]
    df = pd.DataFrame(data=df_dict["data"], columns=df_dict["columns"], index=df_dict["index"])

    log: list[str] = ["Forecast: analyzing lead time trends..."]

    results: dict[str, Any] = {}
    delay_preds: dict[str, Any] = {}

    for sid in df["supplier_id"].unique():
        sub = df[df["supplier_id"] == sid].sort_values("order_date").reset_index(drop=True)
        lead_times = sub["lead_time_days"].values

        # Simple trend: linear regression on index
        x = np.arange(len(lead_times))
        if len(lead_times) > 1:
            slope = np.polyfit(x, lead_times, 1)[0]
        else:
            slope = 0.0

        avg_lt = float(np.mean(lead_times))
        std_lt = float(np.std(lead_times))
        max_lt = float(np.max(lead_times))
        min_lt = float(np.min(lead_times))
        latest_lt = float(lead_times[-1])

        # Predict next order delay (naive: latest + slope)
        predicted_next = latest_lt + slope

        results[sid] = {
            "supplier_name": sub["supplier_name"].iloc[0],
            "order_count": len(sub),
            "avg_lead_time": round(avg_lt, 2),
            "std_lead_time": round(std_lt, 2),
            "trend_slope": round(slope, 3),
            "predicted_next_delay": round(predicted_next, 2),
            "latest_delay": round(latest_lt, 2),
            "max_delay": round(max_lt, 2),
            "min_delay": round(min_lt, 2),
        }

        delay_preds[sid] = {
            "predicted_days": round(predicted_next, 2),
            "confidence": "low" if std_lt > 10 else "medium" if std_lt > 5 else "high",
            "trend": "increasing" if slope > 1 else "decreasing" if slope < -1 else "stable",
        }

    # Save
    out = run_dir / "forecast.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")

    log.append(f"Forecasted {len(results)} suppliers")

    return {
        "forecast_results": results,
        "delay_predictions": delay_preds,
        "log": log,
    }
