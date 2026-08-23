
from __future__ import annotations

from pathlib import Path
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TriageNote:
    content: str
    provider: str
    generated_by: str


def _load_dotenv() -> None:
    """
    Minimal .env loader.

    Does not overwrite environment variables.
    Keeps the application runnable even if python-dotenv
    is not installed.
    """
    env_path = ".env"

    if not os.path.exists(env_path):
        return

    try:
        with open(env_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                os.environ.setdefault(key, value)

    except OSError:
        pass


def _history_payload(history: list[Any]) -> list[dict[str, str]]:
    return [
        {
            "date": event.date,
            "type": event.type,
            "detail": event.detail,
        }
        for event in history
    ]


def _build_input(
    referral,
    relevant_history: list[Any],
) -> dict[str, Any]:
    """
    Deliberately sends only information required to draft
    the triage note.
    """

    return {
        "referral_id": referral.referral_id,
        "summary": referral.summary,
        "requested_action": referral.requested_action,
        "urgency": referral.urgency,
        "received_at": referral.received_at,
        "relevant_history": _history_payload(relevant_history),
    }


def _fallback_note(
    referral,
    relevant_history: list[Any],
) -> str:
    """
    Deterministic fallback.

    This keeps the system functional without an API key.
    """

    history_lines = []

    for event in relevant_history:
        history_lines.append(
            f"- {event.date}: {event.type} — {event.detail}"
        )

    history_text = "\n".join(history_lines)

    if not history_text:
        history_text = "- No relevant history identified."

    return (
        f"Triage note for {referral.referral_id}\n\n"
        f"Referral summary: {referral.summary}\n"
        f"Requested action: {referral.requested_action}\n"
        f"Urgency: {referral.urgency}\n\n"
        f"Relevant case history:\n"
        f"{history_text}\n\n"
        "This note is a proposal for caseworker review and "
        "does not change the resident's case."
    )


def _groq_note(payload: dict[str, Any], api_key: str) -> str:
    model = os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile",
    )

    system_prompt = """
You are drafting a casework triage note.

Produce a concise factual note for a caseworker.

Rules:
- Use ONLY the supplied information.
- Do not invent facts.
- Do not infer eligibility, fraud, misconduct, or other findings.
- Do not make a policy decision.
- Do not claim that an action has been performed.
- Clearly distinguish reported information from established history.
- Keep the note concise and professional.
- State that the note is a proposal for caseworker review.
"""

    user_prompt = json.dumps(payload, indent=2)

    body = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {
                "role": "system",
                "content": system_prompt.strip(),
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    }

    request = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["choices"][0]["message"]["content"].strip()


def _openai_note(payload: dict[str, Any], api_key: str) -> str:
    model = os.getenv(
        "OPENAI_MODEL",
        "gpt-4o-mini",
    )

    system_prompt = """
Draft a concise factual casework triage note.

Use only the supplied information.
Do not invent facts.
Do not make eligibility, fraud, misconduct, or other findings.
Do not perform or claim to perform any case action.
The note is only a proposal for caseworker review.
"""

    body = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {
                "role": "system",
                "content": system_prompt.strip(),
            },
            {
                "role": "user",
                "content": json.dumps(payload, indent=2),
            },
        ],
    }

    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["choices"][0]["message"]["content"].strip()


def generate_triage_note(
    referral,
    relevant_history: list[Any],
) -> TriageNote:
    """
    Generate a triage note.

    Provider selection:
        TRIAGE_LLM_PROVIDER=groq
        TRIAGE_LLM_PROVIDER=openai

    If no provider/key is configured, use deterministic fallback.
    """

    _load_dotenv()

    provider = os.getenv(
        "TRIAGE_LLM_PROVIDER",
        "none",
    ).strip().lower()

    payload = _build_input(
        referral,
        relevant_history,
    )

    try:
        if provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")

            if not api_key:
                return TriageNote(
                    content=_fallback_note(
                        referral,
                        relevant_history,
                    ),
                    provider="none",
                    generated_by="deterministic-fallback",
                )

            content = _groq_note(
                payload,
                api_key,
            )

            return TriageNote(
                content=content,
                provider="groq",
                generated_by="llm",
            )

        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")

            if not api_key:
                return TriageNote(
                    content=_fallback_note(
                        referral,
                        relevant_history,
                    ),
                    provider="none",
                    generated_by="deterministic-fallback",
                )

            content = _openai_note(
                payload,
                api_key,
            )

            return TriageNote(
                content=content,
                provider="openai",
                generated_by="llm",
            )

    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        KeyError,
        json.JSONDecodeError,
    ):
        pass

    return TriageNote(
        content=_fallback_note(
            referral,
            relevant_history,
        ),
        provider="none",
        generated_by="deterministic-fallback",
    )

def save_triage_note(
    referral_id: str,
    note: TriageNote,
    directory: str | Path = "artifacts/triage-notes",
) -> Path:
    """
    Persist a generated triage note for later caseworker review.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    path = directory / f"{referral_id}.md"

    content = (
        f"# Triage Note — {referral_id}\n\n"
        f"**Generated by:** {note.generated_by}\n"
        f"**Provider:** {note.provider}\n\n"
        f"{note.content}\n"
    )

    path.write_text(content, encoding="utf-8")

    return path