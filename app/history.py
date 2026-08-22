from __future__ import annotations

from typing import Any
import urllib.request
import json

from app.models import HistoryEvent, Referral, Resident


class HistoryServiceError(RuntimeError):
    """Raised when the resident history service cannot be used."""


class HistoryClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8083"):
        self.base_url = base_url.rstrip("/")

    def _get(self, path: str) -> dict[str, Any]:
        url = f"{self.base_url}{path}"

        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise HistoryServiceError(
                f"History service request failed: {url}"
            ) from exc

    def health(self) -> dict[str, Any]:
        return self._get("/health")

    def get_resident(self, resident_ref: str) -> Resident:
        data = self._get(f"/residents/{resident_ref}")

        events = [
            HistoryEvent(
                date=event["date"],
                type=event["type"],
                detail=event["detail"],
            )
            for event in data.get("events", [])
        ]

        return Resident(
            resident_ref=data["resident_ref"],
            status=data["status"],
            benefit_code=data["benefit_code"],
            district=data["district"],
            award_monthly=data["award_monthly"],
            household=data.get("household", []),
            events=events,
        )

    def get_events(self, resident_ref: str) -> list[HistoryEvent]:
        data = self._get(f"/residents/{resident_ref}/events")

        return [
            HistoryEvent(
                date=event["date"],
                type=event["type"],
                detail=event["detail"],
            )
            for event in data.get("events", [])
        ]

    def get_household(self, resident_ref: str) -> list[dict[str, Any]]:
        data = self._get(
            f"/residents/{resident_ref}/household"
        )

        return data.get("household", [])


ACTION_KEYWORDS = {
    "review award": {
        "award",
        "payment",
        "review",
        "evidence",
        "income",
        "recalculated",
    },
    "record change of address": {
        "address",
        "contact",
        "correspondence",
    },
    "review household composition": {
        "household",
        "address",
        "evidence",
        "review",
    },
    "draft explanatory note": {
        "payment",
        "award",
        "recalculated",
        "review",
        "contact",
        "evidence",
    },
    "record income change": {
        "income",
        "award",
        "recalculated",
        "employment",
        "evidence",
    },
    "flag for contact attempt": {
        "contact",
        "correspondence",
        "interview",
        "address",
    },
}


def get_relevant_history(
    referral: Referral,
    resident: Resident,
    limit: int = 5,
) -> list[HistoryEvent]:
    """
    Select history events that are relevant to the referral.

    This is deliberately deterministic. The LLM should not receive
    the resident's entire history when only a subset is relevant.
    """

    keywords = ACTION_KEYWORDS.get(
        referral.requested_action.strip().lower(),
        set(),
    )

    if not keywords:
        return resident.events[-limit:]

    scored: list[tuple[int, HistoryEvent]] = []

    for event in resident.events:
        text = (
            f"{event.type} {event.detail}"
        ).lower()

        score = sum(
            1
            for keyword in keywords
            if keyword in text
        )

        if score > 0:
            scored.append((score, event))

    scored.sort(
        key=lambda item: (item[0], item[1].date),
        reverse=True,
    )

    return [
        event
        for _, event in scored[:limit]
    ]