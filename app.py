"""Procurement Intelligence Agent - Streamlit dashboard."""
from pathlib import Path

import streamlit as st

from pia.graph import run_pia

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

    status = st.status("Running PIA pipeline...", expanded=True)
    log_lines: list[str] = []

    def on_event(node_name, update):
        msg = f"**{node_name.upper()}** agent complete"
        if isinstance(update, dict) and update.get("log"):
            msg += f" — {update['log'][-1]}"
        log_lines.append(msg)
        status.write("\n\n".join(log_lines))

    # with st.spinner("Agents working... this may take a few minutes with a local LLM."):
    #     final_state = run_pia(str(data_path), user_prompt, on_event=on_event)
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