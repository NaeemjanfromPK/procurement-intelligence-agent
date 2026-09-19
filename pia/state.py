from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class PIAState(TypedDict, total=False):
    """Channels written by the agents."""
    data_path: str
    user_prompt: str
    run_id: str
    run_dir: str
    supplier_df: dict[str, Any]
    columns: list[str]
    forecast_results: dict[str, Any]
    delay_predictions: dict[str, Any]
    risk_scores: dict[str, Any]
    strategy_recommendations: str
    report_md: str
    report_path: str
    figures: list[str]
    log: Annotated[list[str], operator.add]
    # next_node: str
    # attempts: int


def new_state(data_path: str, user_prompt: str, run_id: str, run_dir: str) -> PIAState:
    return PIAState(
        data_path=data_path,
        user_prompt=user_prompt,
        run_id=run_id,
        run_dir=run_dir,
        # next_node="",
        # attempts=0,
        supplier_df={},
        columns=[],
        forecast_results={},
        delay_predictions={},
        risk_scores={},
        strategy_recommendations="",
        report_md="",
        report_path="",
        figures=[],
        log=[],
    )
