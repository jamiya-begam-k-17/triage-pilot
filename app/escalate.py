from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CasePackage:
    """
    Human-facing package produced after automated triage.

    This contains only information already established by the agent.
    It never authorizes or performs the requested action.
    """

    referral_id: str
    resident_ref: str
    requested_action: str

    status: str
    policy_reference: str
    reason: str

    relevant_history: list[dict[str, Any]]
    household_summary: dict[str, Any]
    missing_information: list[str]

    work_completed: list[str]
    action_taken: str
    action_not_taken: str

    next_human_action: str


class CasePackageStore:
    """
    Persistence boundary for escalation/handoff packages.

    Storage can later be replaced with a database, API, queue, etc.
    """

    def __init__(
        self,
        directory: str | Path = "artifacts/cases",
        index_path: str | Path = "artifacts/cases.json",
    ):
        self.directory = Path(directory)
        self.index_path = Path(index_path)

    def save(self, package: CasePackage) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        data = asdict(package)

        package_path = (
            self.directory / f"{package.referral_id}.json"
        )

        package_path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

        index = self._load_index()

        index = [
            item
            for item in index
            if item.get("referral_id") != package.referral_id
        ]

        index.append(data)

        self.index_path.write_text(
            json.dumps(index, indent=2),
            encoding="utf-8",
        )

    def _load_index(self) -> list[dict[str, Any]]:
        if not self.index_path.exists():
            return []

        try:
            data = json.loads(
                self.index_path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError:
            return []

        if not isinstance(data, list):
            return []

        return data


def _history_to_dict(events) -> list[dict[str, Any]]:
    return [
        {
            "date": event.date,
            "type": event.type,
            "detail": event.detail,
        }
        for event in events
    ]


def _household_summary(
    household: list[dict[str, Any]] | None,
) -> dict[str, Any]:

    if household is None:
        return {
            "status": "UNKNOWN",
            "member_count": None,
        }

    return {
        "status": "ESTABLISHED",
        "member_count": len(household),
    }


def build_case_package(
    referral,
    resident,
    result,
    policy_decision,
) -> CasePackage:
    """
    Build a supervisor/caseworker package.

    This function packages established facts only.
    It does not perform policy evaluation.
    """

    is_escalation = (
        result.status.value == "ESCALATED"
    )

    if is_escalation:
        next_human_action = (
            "Supervisor must review the referral and determine "
            "whether the requested action may proceed."
        )
    else:
        next_human_action = (
            "Caseworker must complete the referral manually. "
            "The assistant must not draft the restricted triage note."
        )

    return CasePackage(
        referral_id=referral.referral_id,
        resident_ref=resident.resident_ref,
        requested_action=referral.requested_action,

        status=result.status.value,
        policy_reference=policy_decision.policy_reference,
        reason=policy_decision.reason,

        relevant_history=_history_to_dict(
            result.relevant_history
        ),

        household_summary=_household_summary(
            resident.household
        ),

        missing_information=list(
            result.missing_information
        ),

        work_completed=[
            "Referral read.",
            "Resident history retrieved.",
            "Relevant history selected.",
            "Household composition evaluated.",
            "Policy decision recorded.",
        ],

        action_taken=result.action_taken,
        action_not_taken=referral.requested_action,

        next_human_action=next_human_action,
    )