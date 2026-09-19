"""Data ingestion agent - loads, validates, and profiles supplier data."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from ..state import PIAState


REQUIRED_COLS = {"supplier_id", "supplier_name", "order_date", "delivery_date", "quantity", "value_usd"}


def ingest_node(state: PIAState) -> dict[str, Any]:
    """Load CSV, validate schema, profile suppliers, write clean data."""
    data_path = Path(state["data_path"])
    run_dir = Path(state["run_dir"])
    run_dir.mkdir(parents=True, exist_ok=True)

    log: list[str] = ["Ingest: loading data..."]

    # Load
    if data_path.suffix.lower() == ".csv":
        df = pd.read_csv(data_path)
    elif data_path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")

    log.append(f"Loaded {len(df)} rows x {len(df.columns)} cols")

    # Validate
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Required: {REQUIRED_COLS}")

    # Parse dates
    for col in ["order_date", "delivery_date"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Compute lead_time_days
    df["lead_time_days"] = (df["delivery_date"] - df["order_date"]).dt.days

    # Basic profile
    profile = {
        "row_count": len(df),
        "supplier_count": df["supplier_id"].nunique(),
        "date_range": [df["order_date"].min().isoformat(), df["order_date"].max().isoformat()],
        "avg_lead_time": round(df["lead_time_days"].mean(), 2),
        "total_value_usd": round(df["value_usd"].sum(), 2),
        "columns": list(df.columns),
    }

    # Save clean data
    clean_path = run_dir / "clean.csv"
    df.to_csv(clean_path, index=False)

    # Save profile
    profile_path = run_dir / "profile.json"
    profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    log.append(f"Suppliers: {profile['supplier_count']}, Avg lead time: {profile['avg_lead_time']} days")

    return {
        "supplier_df": df.to_dict(orient="split"),
        "columns": list(df.columns),
        "log": log,
    }
