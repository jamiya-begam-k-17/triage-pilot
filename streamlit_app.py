"""
TriagePilot — Streamlit UI

This file only wires the UI to the EXISTING backend
(app.workflow.run_workflow / app.agent.TriageAgent). It does not
duplicate, reimplement, or bypass any policy, triage-note, or
safety-gate logic. All referral outcomes, escalation packages,
handoff packages, and triage notes are read directly from what the
backend produces.

Run with:
    streamlit run streamlit_app.py
(from the repository root, so the backend's relative paths resolve.)
"""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from ui.data_access import build_referral_views, load_latest_trace, run_backend_workflow
from ui.service_manager import ensure_history_service_running
from ui.styles import CUSTOM_CSS
from ui.components import (
    render_dashboard,
    render_referral_table,
    render_referral_detail,
    render_full_trace,
)

st.set_page_config(
    page_title="TriagePilot",
    page_icon="🗂️",
    layout="wide",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


NAV_PAGES = ["Dashboard", "Referral queue", "Referral detail", "Execution trace"]


def _init_state() -> None:
    st.session_state.setdefault("views", [])
    st.session_state.setdefault("run_timestamp", None)
    st.session_state.setdefault("last_error", None)
    st.session_state.setdefault("nav_page", NAV_PAGES[0])
    st.session_state.setdefault("selected_referral_id", None)

    # Apply any programmatic navigation request (e.g. from a "View →"
    # row button) BEFORE the radio widget below is instantiated, since
    # a widget's bound session_state key cannot be reassigned after
    # that widget has rendered in the current script run.
    pending = st.session_state.pop("pending_nav", None)
    if pending:
        st.session_state["nav_page"] = pending


def _run_workflow() -> None:
    ok, message = ensure_history_service_running()

    if not ok:
        st.session_state["last_error"] = message
        return

    st.session_state["last_error"] = None

    with st.spinner("Running TriageAgent over the referral queue..."):
        results = run_backend_workflow()
        st.session_state["views"] = build_referral_views(results)
        st.session_state["run_timestamp"] = datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )


_init_state()

# ----------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🗂️ TriagePilot")
    st.caption("Agentic AI for controlled caseworker triage")

    if st.button("▶ Run workflow", width='stretch', type="primary"):
        _run_workflow()

    if st.session_state["last_error"]:
        st.error(st.session_state["last_error"])

    st.divider()

    page = st.radio(
        "View",
        NAV_PAGES,
        label_visibility="collapsed",
        key="nav_page",
    )

    st.divider()
    st.caption(
        "Backend: `app.workflow.run_workflow()`\n\n"
        "Policy: `config/policy.json`\n\n"
        "Safety gates preserved as-is: child-household restriction, "
        "restricted-action approval, ambiguity default-to-approval."
    )

# ----------------------------------------------------------------
# Header
# ----------------------------------------------------------------

st.markdown(
    '<div class="tp-hero"><h1>TriagePilot</h1></div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="tp-subtitle">Controlled, policy-gated triage for casework referrals</div>',
    unsafe_allow_html=True,
)

views = st.session_state["views"]

if not views:
    st.info(
        "No workflow run yet. Click **Run workflow** in the sidebar to "
        "process the referral queue via the existing TriageAgent backend."
    )
    st.stop()

# ----------------------------------------------------------------
# Pages
# ----------------------------------------------------------------

if page == "Dashboard":
    render_dashboard(views, st.session_state["run_timestamp"])
    st.divider()
    render_referral_table(views)

elif page == "Referral queue":
    render_referral_table(views)

elif page == "Referral detail":
    ids = [v.referral_id for v in views]

    default_id = st.session_state.get("selected_referral_id")
    default_index = ids.index(default_id) if default_id in ids else 0

    selected_id = st.selectbox(
        "Select a referral",
        options=ids,
        index=default_index,
        key="referral_detail_select",
    )
    st.session_state["selected_referral_id"] = selected_id

    selected_view = next(v for v in views if v.referral_id == selected_id)
    st.divider()
    render_referral_detail(selected_view)

elif page == "Execution trace":
    render_full_trace(load_latest_trace())
