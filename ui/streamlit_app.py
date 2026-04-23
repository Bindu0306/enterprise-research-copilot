# ui/streamlit_app.py

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from app.orchestrator.graph import run_pipeline
from app.guardrails.output_guard import validate_output
from app.tools.formatter import format_report, format_trace


st.set_page_config(
    page_title="Enterprise Research Copilot",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .agent-trace {
        background-color: #f8f9fa;
        border-left: 3px solid #4CAF50;
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 0 4px 4px 0;
        font-family: monospace;
        font-size: 0.85rem;
        color: #333;
    }
    .agent-error {
        background-color: #fff5f5;
        border-left: 3px solid #f44336;
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 0 4px 4px 0;
        font-family: monospace;
        font-size: 0.85rem;
        color: #c62828;
    }
    .agent-flag {
        background-color: #fff8e1;
        border-left: 3px solid #FFC107;
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 0 4px 4px 0;
        font-family: monospace;
        font-size: 0.85rem;
        color: #e65100;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🔬 Enterprise Research Copilot")
    st.markdown("---")
    st.markdown("#### How it works")
    st.markdown("""
    1. **Planner** breaks your topic into 3 sub-questions
    2. **Researcher** searches Wikipedia for each one
    3. **Critic** evaluates quality and triggers retry if needed
    4. **Writer** generates your structured report
    """)
    st.markdown("---")
    st.markdown("#### Demo Topics")
    demo_topics = [
        "Multi-agent AI systems for business research automation",
        "How AI agents improve enterprise IT operations",
        "Benefits and risks of document intelligence in consulting"
    ]
    st.markdown("Click to use a demo topic:")
    for demo_topic in demo_topics:
        if st.button(demo_topic[:50] + "...", key=demo_topic):
            st.session_state["selected_topic"] = demo_topic
    st.markdown("---")
    st.markdown("#### About")
    st.markdown("""
    Built with:
    - 🦜 LangGraph orchestration
    - 🤖 Groq LLM (Llama 3.3)
    - 📚 Wikipedia API
    - 🛡️ Multi-layer guardrails
    """)

st.markdown('<div class="main-header">🔬 Enterprise Research Copilot</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">A secure multi-agent AI system — Planner · Researcher · Critic · Writer</div>', unsafe_allow_html=True)

default_topic = st.session_state.get("selected_topic", "")

topic = st.text_input(
    "Enter your research topic:",
    value=default_topic,
    placeholder="e.g. How can AI agents improve enterprise IT operations?",
    max_chars=300
)

col1, col2 = st.columns([2, 1])

with col1:
    run_button = st.button("🚀 Run Research Pipeline", type="primary", use_container_width=True)

with col2:
    clear_button = st.button("🗑️ Clear", use_container_width=True)

if clear_button:
    st.session_state.clear()
    st.rerun()

if run_button and topic:

    st.markdown("---")
    st.markdown("### ⚡ Pipeline Running")

    status_cols = st.columns(4)
    with status_cols[0]:
        planner_status = st.empty()
        planner_status.info("⏳ Planner")
    with status_cols[1]:
        researcher_status = st.empty()
        researcher_status.info("⏳ Researcher")
    with status_cols[2]:
        critic_status = st.empty()
        critic_status.info("⏳ Critic")
    with status_cols[3]:
        writer_status = st.empty()
        writer_status.info("⏳ Writer")

    with st.spinner("Agents are collaborating..."):
        try:
            state = run_pipeline(topic)
        except Exception as e:
            st.error(f"Pipeline crashed: {e}")
            st.stop()

    trace = state.get("trace", [])

    planner_done    = any("Planner: created" in t for t in trace)
    researcher_done = any("Researcher: complete" in t for t in trace)
    critic_done     = any("Critic: evaluation complete" in t for t in trace)
    writer_done     = any("Writer: report generated" in t for t in trace)
    retry_happened  = any("Retry triggered" in t for t in trace)

    if planner_done:
        planner_status.success("✅ Planner")
    else:
        planner_status.error("❌ Planner")

    if researcher_done:
        if retry_happened:
            researcher_status.warning("🔄 Researcher (retried)")
        else:
            researcher_status.success("✅ Researcher")
    else:
        researcher_status.error("❌ Researcher")

    if critic_done:
        critic_status.success("✅ Critic")
    else:
        critic_status.error("❌ Critic")

    if writer_done:
        writer_status.success("✅ Writer")
    else:
        writer_status.error("❌ Writer")

    if state.get("error"):
        st.error(f"❌ Pipeline Error: {state['error']}")
        st.stop()

    st.markdown("---")
    st.markdown("### 📊 Results")

    confidence     = state.get("confidence_score", 0)
    retry_count    = state.get("retry_count", 0)
    findings_count = len(state.get("findings", []))
    report_length  = len(state.get("final_report", ""))

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        if confidence >= 0.65:
            conf_label = "Good"
        elif confidence >= 0.45:
            conf_label = "Moderate"
        else:
            conf_label = "Low"
        st.metric("Research Confidence", f"{confidence:.0%}", delta=conf_label)

    with m2:
        st.metric("Findings", findings_count, delta="from Wikipedia")

    with m3:
        st.metric("Retry Triggered", "Yes" if retry_count > 0 else "No", delta=f"attempt {retry_count + 1}")

    with m4:
        st.metric("Report Size", f"{report_length} chars", delta="generated")

    with st.expander("📋 Research Plan (Planner Output)", expanded=False):
        subquestions = state.get("subquestions", [])
        if subquestions:
            for i, q in enumerate(subquestions):
                st.markdown(f"**{i+1}.** {q}")
        else:
            st.warning("No sub-questions generated")

    with st.expander("🔍 Agent Execution Trace", expanded=False):
        formatted_trace = format_trace(trace)
        for entry in formatted_trace:
            if "ERROR" in entry:
                st.markdown(f'<div class="agent-error">{entry}</div>', unsafe_allow_html=True)
            elif "flagged" in entry.lower() or "retry" in entry.lower():
                st.markdown(f'<div class="agent-flag">{entry}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="agent-trace">{entry}</div>', unsafe_allow_html=True)

    st.markdown("### 📄 Research Report")

    raw_report = state.get("final_report", "")
    is_valid, clean_report = validate_output(raw_report)

    if not is_valid:
        st.error(f"Report validation failed: {clean_report}")
    else:
        formatted = format_report(clean_report)
        st.markdown(formatted)

        st.markdown("**Download Report:**")
        dl1, dl2 = st.columns(2)
        safe_topic = topic[:30].replace(' ', '_')

        with dl1:
            st.download_button(
                label="📄 Download Markdown",
                data=formatted,
                file_name=f"report_{safe_topic}.md",
                mime="text/markdown",
                use_container_width=True
            )

        with dl2:
            st.download_button(
                label="📝 Download Text",
                data=formatted,
                file_name=f"report_{safe_topic}.txt",
                mime="text/plain",
                use_container_width=True
            )

elif run_button and not topic:
    st.warning("⚠️ Please enter a research topic first.")

st.markdown("---")
st.markdown(
    "<center><small>Enterprise Research Copilot · Multi-Agent AI System · "
    "Built with LangGraph + Groq + Wikipedia + Streamlit</small></center>",
    unsafe_allow_html=True
)