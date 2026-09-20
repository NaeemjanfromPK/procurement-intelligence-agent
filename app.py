"""Procurement Intelligence Agent - Streamlit dashboard."""
from pathlib import Path
import streamlit as st
import pandas as pd
from pia.graph import run_pia

REQUIRED_COLS = {
    "supplier_id": "Unique ID per supplier — used to group orders and score risk per supplier.",
    "supplier_name": "Human-readable name — shown in reports and strategies.",
    "order_date": "When the order was placed — baseline for lead-time calculation.",
    "delivery_date": "When it arrived — combined with order_date to compute `lead_time_days`, the core forecasting signal.",
    "quantity": "Units ordered — used for volume-weighted analysis.",
    "value_usd": "Order value — drives spend-share and cost-impact framing in the report.",
}

def check_dataset(path: Path) -> tuple[list[str], list[str]]:
    """Returns (blocking_errors, warnings) for the uploaded CSV."""
    errors: list[str] = []
    warnings: list[str] = []
    df = pd.read_csv(path)
    n = len(df)
    if n == 0:
        errors.append("The file has **no data rows** — only a header.")
        return errors, warnings

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    for c in missing:
        errors.append(f"`{c}` — {REQUIRED_COLS[c]}")

    if not errors:
        for c in REQUIRED_COLS:
            empty = df[c].isna().sum()
            if empty:
                warnings.append(f"`{c}`: {empty} empty cells ({empty / n * 100:.1f}%)")
        for c in ("order_date", "delivery_date"):
            bad = pd.to_datetime(df[c], errors="coerce").isna().sum()
            if bad:
                warnings.append(f"`{c}`: {bad} values aren't valid dates")
    return errors, warnings



st.set_page_config(page_title="PIA - Procurement Intelligence", page_icon="📦", layout="wide")

st.title("📦 Procurement Intelligence Agent")
st.caption("Multi-agent supply chain risk analysis: ingest → forecast + risk → strategy → report")

with st.sidebar:
    st.header("Run Analysis")
    uploaded = st.file_uploader("Upload supplier data (CSV)", type=["csv"])
    use_sample = st.toggle("Use sample data", value=uploaded is None)
    user_prompt = st.text_area(
        "Analysis focus",
        value="Analyze supplier risk and recommend procurement strategies.",
    )
    run_clicked = st.button("🚀 Run PIA", type="primary", use_container_width=True)

if run_clicked:
    if uploaded is not None and not use_sample:
        data_dir = Path("runs/_uploads")
        data_dir.mkdir(parents=True, exist_ok=True)
        data_path = data_dir / uploaded.name
        data_path.write_bytes(uploaded.getbuffer())
    else:
        data_path = Path("data/sample_suppliers.csv")

    # ─── NEW: pre-flight validation goes here ───
    errors, warnings = check_dataset(data_path)

    if errors:
        st.error("⚠️ Your dataset is missing columns PIA needs:")
        for e in errors:
            st.markdown(f"- {e}")
        st.info("💡 Fix your CSV and re-upload. Or use the sample data toggle to see PIA in action.")
        st.stop()

    if warnings:
        st.warning("Dataset loaded, but heads-up:\n\n" + "\n\n".join(f"- {w}" for w in warnings))
    # ─── end of new code ───

    status = st.status("Running PIA pipeline...", expanded=True)

    log_lines: list[str] = []

    def on_event(node_name, update):
        msg = f"**{node_name.upper()}** agent complete"
        if isinstance(update, dict) and update.get("log"):
            msg += f" — {update['log'][-1]}"
        log_lines.append(msg)
        status.write("\n\n".join(log_lines))

    try:
        with st.spinner("Agents working... this may take a few minutes with a local LLM."):
            final_state = run_pia(str(data_path), user_prompt, on_event=on_event)
    except Exception as exc:
        status.update(label="❌ Pipeline failed", state="error")
        st.error(f"Pipeline error: {exc}")
        st.info("💡 The live demo UI is running on Streamlit Cloud, but the LLM pipeline "
                "needs a local Ollama instance. Clone the repo and run: "
                "`ollama pull qwen2.5-coder:7b` then `streamlit run app.py`")
        st.stop()
         
    status.update(label="✅ Pipeline complete", state="complete")

    st.success(f"Run ID: `{final_state['run_id']}`")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📋 Executive Report")
        st.markdown(final_state.get("report_md", "_No report generated._"))
    with col2:
        st.subheader("🎯 Strategy")
        st.markdown(final_state.get("strategy_recommendations", "_No strategy generated._"))
        if final_state.get("risk_scores"):
            st.subheader("🔍 Risk Scores (raw)")
            st.json(final_state["risk_scores"])

    report_path = final_state.get("report_path")
    if report_path and Path(report_path).exists():
        st.download_button(
            "⬇️ Download report.md",
            data=Path(report_path).read_bytes(),
            file_name="report.md",
            mime="text/markdown",
        )
else:
    st.info("👈 Upload a CSV (or use the sample) and hit **Run PIA** to start the analysis.")