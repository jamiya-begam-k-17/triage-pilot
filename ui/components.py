"""
Rendering components for the TriagePilot Streamlit UI.

These functions only display data already produced by the backend
(app.workflow / app.agent.TriageAgent and the artifacts it writes).
No policy, eligibility, or triage-note logic is implemented here.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import streamlit as st

from ui.data_access import ReferralView, trace_for_referral
from ui.styles import status_badge

STATUS_ORDER = ["COMPLETED", "ESCALATED", "HANDOFF", "FAILED"]


# --------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------

def render_dashboard(views: list[ReferralView], run_timestamp: str | None) -> None:
    counts = Counter(v.status for v in views)

    st.markdown("### Latest workflow run")
    ts_label = run_timestamp or "No run yet"
    st.caption(f"Run completed: {ts_label}  ·  {len(views)} referrals processed")

    cols = st.columns(4)
    metric_config = [
        ("COMPLETED", "✅ Completed", "Permitted actions executed"),
        ("ESCALATED", "🛑 Escalated", "Blocked pending supervisor approval"),
        ("HANDOFF", "🧑‍💼 Handoff", "Sent to caseworker queue"),
        ("FAILED", "⚠️ Failed", "Errored without halting the run"),
    ]

    for col, (key, label, help_text) in zip(cols, metric_config):
        with col:
            st.metric(label, counts.get(key, 0), help=help_text)

    st.markdown("&nbsp;", unsafe_allow_html=True)

    if views:
        dist = pd.DataFrame(
            [{"Status": s, "Count": counts.get(s, 0)} for s in STATUS_ORDER]
        )
        st.bar_chart(dist.set_index("Status"), height=220)


# --------------------------------------------------------------------
# Referral table
# --------------------------------------------------------------------

def render_referral_table(views: list[ReferralView]) -> None:
    st.markdown("### Referral queue")
    st.caption("Click any row to open its full detail view.")

    search_col, filter_col = st.columns([2, 3])

    with search_col:
        search = st.text_input(
            "Search",
            placeholder="Search by referral ID, resident, or action…",
            label_visibility="collapsed",
        )

    with filter_col:
        status_filter = st.multiselect(
            "Filter by status",
            options=STATUS_ORDER,
            default=STATUS_ORDER,
            label_visibility="collapsed",
            placeholder="Filter by status",
        )

    filtered = [v for v in views if v.status in status_filter]

    if search:
        needle = search.strip().lower()
        filtered = [
            v
            for v in filtered
            if needle in v.referral_id.lower()
            or needle in v.resident_ref.lower()
            or needle in v.requested_action.lower()
        ]

    if not filtered:
        st.info("No referrals match the current filter.")
        return

    st.caption(f"{len(filtered)} of {len(views)} referrals shown")

    # Header row
    header = st.columns([1.3, 1.3, 1.2, 2.1, 3, 1.6, 0.9])
    for col, label in zip(
        header,
        [
            "Status",
            "Referral ID",
            "Resident",
            "Requested action",
            "Reason",
            "Action taken",
            "",
        ],
    ):
        col.markdown(f"**{label}**")

    st.markdown(
        '<hr style="margin:0.2rem 0 0.6rem 0; border-color:#e5e7eb;">',
        unsafe_allow_html=True,
    )

    for v in filtered:
        row = st.columns([1.3, 1.3, 1.2, 2.1, 3, 1.6, 0.9])

        row[0].markdown(status_badge(v.status), unsafe_allow_html=True)
        row[1].markdown(f"**{v.referral_id}**")
        row[2].write(v.resident_ref)
        row[3].write(v.requested_action)
        row[4].write(v.reason)
        row[5].write(v.action_taken)

        if row[6].button("View →", key=f"view_{v.referral_id}", width='stretch'):
            st.session_state["selected_referral_id"] = v.referral_id
            st.session_state["pending_nav"] = "Referral detail"
            st.rerun()

        st.markdown(
            '<hr style="margin:0.35rem 0; border-color:#f1f2f4;">',
            unsafe_allow_html=True,
        )


# --------------------------------------------------------------------
# Referral detail
# --------------------------------------------------------------------

def _render_history(history: list[dict[str, Any]]) -> None:
    if not history:
        st.caption("No relevant history was selected for this referral.")
        return

    for event in history:
        st.markdown(
            f"- **{event.get('date', '?')}** · {event.get('type', '?')} — "
            f"{event.get('detail', '')}"
        )


def _render_trace(referral_id: str) -> None:
    events = trace_for_referral(referral_id)

    if not events:
        st.caption("No audit trace entries found for this referral.")
        return

    for event in events:
        step = event.get("step", "")
        message = event.get("message", "")
        data = {
            k: v
            for k, v in (event.get("data") or {}).items()
            if k not in ("referral_id",)
        }

        st.markdown(
            f'<div class="tp-trace-step">'
            f'<span class="step-label">{step}</span><br/>{message}'
            f"</div>",
            unsafe_allow_html=True,
        )

        if data:
            with st.expander("Details", expanded=False):
                st.json(data)


def render_referral_detail(view: ReferralView) -> None:
    st.markdown(
        f"## {view.referral_id} &nbsp; {status_badge(view.status)}",
        unsafe_allow_html=True,
    )
    st.caption(
        f"Resident **{view.resident_ref}** · Source: {view.source} · "
        f"Urgency: {view.urgency} · Received: {view.received_at}"
    )

    with st.container(border=True):
        st.markdown("**Referral summary**")
        st.write(view.summary)
        st.markdown(f"**Requested action:** {view.requested_action}")
        st.markdown(f"**Policy reason:** {view.reason}")

    tabs = st.tabs(
        ["Outcome", "Relevant history", "Execution trace", "Policy & what wasn't done"]
    )

    with tabs[0]:
        _render_outcome(view)

    with tabs[1]:
        _render_history(view.relevant_history)

    with tabs[2]:
        _render_trace(view.referral_id)

    with tabs[3]:
        _render_policy_and_omissions(view)


def _render_outcome(view: ReferralView) -> None:
    if view.status == "COMPLETED":
        _render_completed_outcome(view)
    elif view.status == "ESCALATED":
        _render_escalated_outcome(view)
    elif view.status == "HANDOFF":
        _render_handoff_outcome(view)
    else:
        st.warning(
            "This referral failed during processing and no action was taken. "
            f"Reason: {view.reason}"
        )


def _render_completed_outcome(view: ReferralView) -> None:
    st.success(f"Action taken: **{view.action_taken}**")

    generated_by = view.triage_note_generated_by or "unknown"
    provider = view.triage_note_provider or "unknown"

    badge = "🤖 LLM-generated" if generated_by == "llm" else "🧮 Deterministic fallback"
    st.markdown(
        f"**Triage note** &nbsp; <span class='tp-pill'>{badge}</span> "
        f"<span class='tp-pill'>provider: {provider}</span>",
        unsafe_allow_html=True,
    )

    if view.triage_note:
        st.markdown(
            f'<div class="tp-note-box">{view.triage_note}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.caption("No triage note content was recorded for this referral.")


def _render_escalated_outcome(view: ReferralView) -> None:
    st.markdown(
        '<div class="tp-not-done">🛑 HARD STOP — '
        f'requested action "{view.requested_action}" was BLOCKED pending '
        "supervisor approval. No action was taken.</div>",
        unsafe_allow_html=True,
    )

    pkg = view.escalation_package or {}

    st.markdown("#### Supervisor escalation package")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Policy reference:** {pkg.get('policy_reference', '—')}")
        st.markdown(f"**Status:** {pkg.get('status', view.status)}")
    with col2:
        st.markdown(f"**Action taken:** {pkg.get('action_taken', 'NONE')}")
        st.markdown(
            f"**Action NOT taken:** {pkg.get('action_not_taken', view.requested_action)}"
        )

    st.markdown(f"**Next human action:** {pkg.get('next_human_action', '—')}")

    work_completed = pkg.get("work_completed") or []
    if work_completed:
        st.markdown("**Work completed prior to hard stop:**")
        for item in work_completed:
            st.markdown(f"- {item}")

    household = pkg.get("household_summary")
    if household:
        st.markdown(
            f"**Household summary:** {household.get('status', '—')} "
            f"({household.get('member_count', '—')} members)"
        )

    missing = pkg.get("missing_information") or []
    if missing:
        st.markdown("**Missing information:**")
        for item in missing:
            st.markdown(f"- {item}")

    with st.expander("Raw escalation package (JSON)"):
        st.json(pkg)


def _render_handoff_outcome(view: ReferralView) -> None:
    st.markdown(
        '<div class="tp-not-done">🧑‍💼 HARD STOP — case handed off to a '
        "caseworker. NO triage note was generated for this referral.</div>",
        unsafe_allow_html=True,
    )

    pkg = view.handoff_package or {}

    st.markdown("#### Caseworker handoff package")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Requested action:** {pkg.get('requested_action', '—')}")
        st.markdown(f"**Urgency:** {pkg.get('urgency', '—')}")
    with col2:
        st.markdown(f"**Next step:** {pkg.get('next_step', '—')}")

    resident_info = pkg.get("resident") or {}
    if resident_info:
        st.markdown(
            f"**Resident status:** {resident_info.get('status', '—')} · "
            f"Benefit: {resident_info.get('benefit_code', '—')} · "
            f"District: {resident_info.get('district', '—')}"
        )

    household = pkg.get("household") or []
    if household:
        st.markdown("**Household composition:**")
        hh_df = pd.DataFrame(household)
        st.dataframe(hh_df, width='stretch', hide_index=True)

    with st.expander("Raw handoff package (JSON)"):
        st.json(pkg)


def _render_policy_and_omissions(view: ReferralView) -> None:
    st.markdown("#### Policy decision")
    st.markdown(f"**Reason given by policy engine:** {view.reason}")

    pkg = view.escalation_package or view.handoff_package
    if pkg and "policy_reference" in pkg:
        st.markdown(f"**Policy reference:** {pkg['policy_reference']}")

    st.markdown("#### What the agent did NOT do")

    if view.status == "COMPLETED":
        st.info(
            "This referral was permitted, so the agent did not withhold any "
            "action. Only the requested action was performed; no additional "
            "actions (e.g. payment/award changes) were taken."
        )
    elif view.status == "ESCALATED":
        st.error(
            f"The agent did **not** perform: *{view.requested_action}*. "
            "This remains blocked until a supervisor approves it."
        )
    elif view.status == "HANDOFF":
        st.error(
            f"The agent did **not** perform: *{view.requested_action}*, and "
            "did **not** draft a triage note, per the child-household "
            "safety restriction."
        )
    else:
        st.error("No action was performed because this referral failed to process.")

    if view.missing_information:
        st.markdown("**Missing information noted by the agent:**")
        for item in view.missing_information:
            st.markdown(f"- {item}")


# --------------------------------------------------------------------
# Full audit trace
# --------------------------------------------------------------------

def render_full_trace(trace_events: list[dict[str, Any]]) -> None:
    st.markdown("### Latest execution trace")

    if not trace_events:
        st.info("No trace available yet. Run the workflow first.")
        return

    referral_ids = sorted(
        {
            e.get("data", {}).get("referral_id")
            for e in trace_events
            if e.get("data", {}).get("referral_id")
        }
    )

    focus = st.selectbox(
        "Focus on a referral (optional)",
        options=["All referrals"] + referral_ids,
    )

    events = trace_events
    if focus != "All referrals":
        events = [
            e for e in trace_events if e.get("data", {}).get("referral_id") == focus
        ]

    for event in events:
        step = event.get("step", "")
        message = event.get("message", "")
        data = event.get("data") or {}

        st.markdown(
            f'<div class="tp-trace-step">'
            f'<span class="step-label">{step}</span><br/>{message}'
            f"</div>",
            unsafe_allow_html=True,
        )

        if data:
            with st.expander("Details", expanded=False):
                st.json(data)
