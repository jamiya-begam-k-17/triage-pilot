"""Custom CSS for a clean, professional, hackathon-demo-quality UI."""

CUSTOM_CSS = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    h1, h2, h3 {
        font-weight: 650;
        letter-spacing: -0.01em;
    }

    .tp-hero {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.25rem;
    }

    .tp-subtitle {
        color: #6b7280;
        font-size: 0.95rem;
        margin-top: -0.4rem;
        margin-bottom: 1.4rem;
    }

    .status-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        white-space: nowrap;
    }
    .status-COMPLETED { background: #dcfce7; color: #15803d; }
    .status-ESCALATED { background: #fee2e2; color: #b91c1c; }
    .status-HANDOFF   { background: #fef3c7; color: #92400e; }
    .status-FAILED    { background: #e5e7eb; color: #374151; }

    .tp-card {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        background: #ffffff;
        margin-bottom: 0.9rem;
    }

    .tp-card-title {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #6b7280;
        margin-bottom: 0.5rem;
    }

    .tp-not-done {
        border-left: 4px solid #b91c1c;
        background: #fef2f2;
        padding: 0.7rem 1rem;
        border-radius: 6px;
        color: #7f1d1d;
        font-weight: 600;
    }

    .tp-hard-stop {
        border-left: 4px solid #d97706;
        background: #fffbeb;
        padding: 0.7rem 1rem;
        border-radius: 6px;
        color: #78350f;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }

    .tp-note-box {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        white-space: pre-wrap;
        font-family: "Source Serif Pro", Georgia, serif;
        line-height: 1.55;
    }

    .tp-pill {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
        background: #eef2ff;
        color: #3730a3;
        margin-left: 6px;
    }

    .tp-trace-step {
        border-left: 3px solid #d1d5db;
        padding: 0.35rem 0 0.35rem 0.9rem;
        margin-bottom: 0.35rem;
    }
    .tp-trace-step .step-label {
        font-weight: 700;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        color: #4b5563;
    }
</style>
"""


def status_badge(status: str) -> str:
    return f'<span class="status-badge status-{status}">{status}</span>'
