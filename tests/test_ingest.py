"""Tests for the ingest agent - fast, offline, no LLM calls."""
from pathlib import Path

import pandas as pd
import pytest

from pia.agents.ingest import ingest_node, REQUIRED_COLS
from pia.state import new_state

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CSV = PROJECT_ROOT / "data" / "sample_suppliers.csv"


@pytest.fixture()
def ingest_result(tmp_path):
    state = new_state(
        data_path=str(SAMPLE_CSV),
        user_prompt="Analyze supplier risk",
        run_id="test_ingest",
        run_dir=str(tmp_path),
    )
    return ingest_node(state), tmp_path


def test_returns_required_keys(ingest_result):
    result, _ = ingest_result
    assert "supplier_df" in result
    assert "columns" in result
    assert "log" in result


def test_writes_clean_csv_and_profile(ingest_result):
    _, run_dir = ingest_result
    clean = pd.read_csv(run_dir / "clean.csv")
    assert set(REQUIRED_COLS).issubset(clean.columns)
    assert "lead_time_days" in clean.columns
    assert (clean["lead_time_days"] >= 0).all()
    assert (run_dir / "profile.json").exists()


def test_log_records_progress(ingest_result):
    result, _ = ingest_result
    log = result["log"]
    assert any("loading" in entry for entry in log)
    assert any("Suppliers" in entry for entry in log)