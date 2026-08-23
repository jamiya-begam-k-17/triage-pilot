# TriagePilot

Agentic AI for **controlled** caseworker triage — an agent that reads a
referral, checks it against policy, and only ever does one of three
things: complete the permitted action, hard-stop and escalate to a
supervisor, or hard-stop and hand off to a human caseworker. It never
takes a restricted action on its own, and it never drafts a note for a
household it isn't allowed to.

A Streamlit UI sits on top of the same backend to make a run easy to
demo and audit.

---

## Requirements

- Python 3.10+
- No external services required to run the core demo — the "resident
  history" API is a small local mock server included in this repo
  (`challenge/services/history_service.py`).
- Optional: a [Groq](https://console.groq.com) API key, only needed if
  you want LLM-generated triage notes instead of the deterministic
  fallback (see [LLM triage notes](#llm-triage-notes-optional) below).

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/jamiya-begam-k-17/triage-pilot.git
cd triage-pilot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Streamlit demo

```bash
streamlit run streamlit_app.py
```

Open the URL Streamlit prints (typically `http://localhost:8501`),
then click **▶ Run workflow** in the sidebar. This executes the real
backend (`app.workflow.run_workflow()`) against
`challenge/referral-queue.json` and displays the results — dashboard
counts, the referral queue, per-referral detail (trace, history,
policy decision, triage note or escalation/handoff package), and the
full audit trace.

## **Optional: Run the backend directly**

**Terminal 1**
```
python challenge/services/history_service.py --port 8083
```

**Terminal 2**
```bash
python -m app.main
```

This runs the same backend workflow and prints a one-line summary per
referral. Full output is written to `artifacts/latest-run.md` and
`artifacts/latest-run.json`, plus per-referral case packages under
`artifacts/cases/` and triage notes under `artifacts/triage-notes/`.

### 4. Run tests

```bash
pip install pytest
pytest tests/ -q
```

---

## LLM triage notes

By default, triage notes for `COMPLETED` referrals are generated with
a **deterministic fallback** — no API key needed, no external calls
made. This is enough to run the full demo end to end.

To generate notes with an LLM instead, we use **Groq**:

```bash
cp .env.example .env
```

Then edit `.env`:

```bash
TRIAGE_LLM_PROVIDER=groq
GROQ_API_KEY=your-key-here
GROQ_MODEL=llama-3.3-70b-versatile   # optional override
```

If `GROQ_API_KEY` is missing, unset, or the Groq call fails for any
reason, the agent **automatically falls back to the deterministic
note** rather than failing the referral — this is a safety property
of the backend, not a UI feature. Every triage note (in the UI and in
`artifacts/triage-notes/*.md`) is labeled with whether it was
`llm`-generated or `deterministic-fallback`, and which provider was
used, so this is always visible and auditable.

---

## Troubleshooting

- **"Connection refused" / history lookups fail** — the mock service
  in step 2 isn't running. Start it, or just use the Streamlit UI,
  which starts it automatically.
- **`ModuleNotFoundError: No module named 'app'`** — run commands
  from the repository root, and use `python -m app.main` (not
  `python app/main.py`) so the `app` package resolves correctly.
- **Streamlit shows "No workflow run yet"** — click **▶ Run
  workflow** in the sidebar; nothing runs automatically on page load.
- **Port 8083 already in use** — another instance of the history
  service is likely still running from a previous session; stop it
  or change `--port` (and update `HISTORY_SERVICE_URL` in
  `ui/service_manager.py` / the corresponding constant in
  `app/history.py` to match).

---

## Architecture

TriagePilot follows a deterministic **UNDERSTAND → DECIDE → ACT** pipeline.

```text
                         ┌──────────────────────┐
                         │  Overnight Referrals |
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │        UNDERSTAND           │
                    │                             │
                    │  • Read referral            │
                    │  • Retrieve resident        │
                    │    history                  │
                    │  • Select relevant history  │
                    │  • Identify requested action│
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │          DECIDE             │
                    │                             │
                    │     Deterministic Policy    │
                    │          Evaluator          │
                    └──────────────┬──────────────┘
                                   │
                  ┌────────────────┼────────────────┐
                  │                │                │
                  ▼                ▼                ▼
            ┌──────────┐    ┌──────────────┐   ┌──────────┐
            │PERMITTED │    │   REQUIRES   │   │ HANDOFF  │
            │          │    │   APPROVAL   │   │          │
            └────┬─────┘    └──────┬───────┘   └────┬─────┘
                 │                 │                │
                 ▼                 ▼                ▼
        ┌────────────────┐  ┌──────────────┐  ┌──────────────┐
        │  TRIAGE NOTE   │  │ Escalation   │  │ Caseworker   │
        │   Generation   │  │   Package    │  │   Handoff    │
        │                │  │              │  │              │
        │  Groq LLM or   │  │ HARD STOP    │  │ HARD STOP    │
        │ deterministic  │  │              │  │              │
        │   fallback     │  │ Human review │  │ Human review │
        └───────┬────────┘  └──────┬───────┘  └──────┬───────┘
                │                  │                 │
                └──────────────────┼─────────────────┘
                                   ▼
                    ┌─────────────────────────────┐
                    │       AUDIT / TRACE         │
                    │                             │
                    │  Decision • Reason • Action │
                    │  History • Hard Stops       │
                    │  Escalation • Handoff       │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │       Streamlit UI          │
                    │                             │
                    │ Dashboard • Referrals       │
                    │ Notes • Decisions • Trace   │
                    └─────────────────────────────┘
```

## Safety and Guardrails

Authority is enforced in `app/policy.py` against `config/policy.json`, in this precedence:

1. **Child-household restriction (ACA-2026/2 §3.9)** — highest precedence. If any household member is under 18, or household composition/age cannot be established, the referral is handed off and **no triage note is drafted at all**, not even as a draft. This was added on day two — see `DECISIONS.md`.
2. **Restricted actions (ACA-2026/1 §3)** — keyword-matched (payment/bank/card details, award changes, suspend/terminate/reinstate). Blocked pending supervisor approval; an escalation package is built and saved, the action is never performed even partially.
3. **Permitted actions (ACA-2026/1 §2)** — reading, retrieving history, categorising, and drafting a proposal note proceed automatically.
4. **Ambiguity (ACA-2026/1 §6.1)** — anything not explicitly permitted defaults to requiring approval. There is no fourth path.

Escalation and handoff are kept distinct per ACA-2026/2 §3.3: an escalation asks whether the Department may act at all; a handoff is ordinary casework a person must do. Every decision, and the information it was based on, is written to the audit trail regardless of outcome.

## Project Structure

```
app/                     Backend: agent, policy engine, workflow, triage notes
challenge/
  referral-queue.json    Input referrals for the demo run
  services/
    history_service.py   Local mock resident-history API (no external calls)
config/policy.json        Policy rules the agent enforces
ui/                        Streamlit UI: data access, components, styling
streamlit_app.py           Streamlit entry point
tests/                     Unit tests for policy, history, referrals
artifacts/                 Generated on each run: audit trace, case packages,
                            triage notes (git-ignored, created automatically)
```

## Limitations

- Referral-to-history relevance matching (`app/history.py`) is keyword-based, not semantic — it will miss history that's relevant but doesn't share vocabulary with the requested action.
- The LLM-backed triage note is a thin wrapper over Groq LLM chat completions with no retry/backoff beyond a single try/except fallback; a transient API failure silently falls back to the deterministic note rather than retrying.
- No persistence layer beyond flat JSON/Markdown files in `artifacts/` — fine for a 12-referral demo queue, not for production volume or concurrent runs.
- The Streamlit dashboard is read/trigger-only; it has no auth and isn't meant to be exposed beyond a local demo.
- Restricted-action matching is substring-based (`config/policy.json`), so it can both over- and under-match on phrasing outside the provided data pack.

## AI Usage

See [AI-USAGE.md](AI-USAGE.md).

## Engineering Decisions

See [DECISIONS.md](DECISIONS.md).