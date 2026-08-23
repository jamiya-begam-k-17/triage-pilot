from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class PolicyStatus(str, Enum):
    PERMITTED = "PERMITTED"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
    HANDOFF = "HANDOFF"


@dataclass(frozen=True)
class PolicyDecision:
    status: PolicyStatus
    reason: str
    policy_reference: str


POLICY_PATH = (
    Path(__file__).resolve().parent.parent / "config" / "policy.json"
)


def _load_policy() -> dict[str, Any]:
    try:
        with POLICY_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Unable to load policy from {POLICY_PATH}"
        ) from exc


POLICY = _load_policy()


def _parse_reference_date(received_at: str | None) -> date:
    if not received_at:
        return date.today()

    try:
        return datetime.fromisoformat(received_at).date()
    except ValueError:
        return date.today()


def _is_under_18(
    date_of_birth: str,
    reference_date: date,
) -> bool:
    try:
        dob = date.fromisoformat(date_of_birth)
    except (TypeError, ValueError):
        raise ValueError("Invalid or missing date of birth")

    age = reference_date.year - dob.year

    if (reference_date.month, reference_date.day) < (
        dob.month,
        dob.day,
    ):
        age -= 1

    return age < 18


def _evaluate_household(
    household: list[dict[str, Any]] | None,
    received_at: str | None,
) -> PolicyDecision | None:

    child_policy = POLICY["child_household"]

    # ACA-2026/2 §5.2
    if household is None:
        return PolicyDecision(
            status=PolicyStatus.HANDOFF,
            reason=child_policy["unknown_household_reason"],
            policy_reference=child_policy["unknown_household_reference"],
        )

    reference_date = _parse_reference_date(received_at)

    for member in household:
        dob = member.get("date_of_birth")

        # ACA-2026/2 §5.2
        if not dob:
            return PolicyDecision(
                status=PolicyStatus.HANDOFF,
                reason=child_policy["missing_age_reason"],
                policy_reference=child_policy["unknown_household_reference"],
            )

        try:
            if _is_under_18(dob, reference_date):
                return PolicyDecision(
                    status=PolicyStatus.HANDOFF,
                    reason=child_policy["child_reason"],
                    policy_reference=child_policy["policy_reference"],
                )
        except ValueError:
            return PolicyDecision(
                status=PolicyStatus.HANDOFF,
                reason=child_policy["missing_age_reason"],
                policy_reference=child_policy["unknown_household_reference"],
            )

    return None


def evaluate_action(
    requested_action: str,
    household: list[dict[str, Any]] | None = None,
    received_at: str | None = None,
) -> PolicyDecision:

    action = requested_action.strip().lower()

    # 1. Child-household restriction has highest precedence.
    household_decision = _evaluate_household(
        household=household,
        received_at=received_at,
    )

    if household_decision is not None:
        return household_decision

    # 2. Restricted actions.
    for rule in POLICY["restricted_actions"]:
        if rule["match"] in action:
            return PolicyDecision(
                status=PolicyStatus.REQUIRES_APPROVAL,
                reason=rule["reason"],
                policy_reference=rule["policy_reference"],
            )

    # 3. Explicitly permitted actions.
    if action in POLICY["permitted_actions"]:
        return PolicyDecision(
            status=PolicyStatus.PERMITTED,
            reason="Action is permitted under ACA-2026/1 §2.",
            policy_reference="ACA-2026/1 §2",
        )

    # 4. ACA-2026/1 §6.1 — ambiguity defaults to approval.
    ambiguity = POLICY["ambiguity"]

    return PolicyDecision(
        status=PolicyStatus.REQUIRES_APPROVAL,
        reason=ambiguity["reason"],
        policy_reference=ambiguity["policy_reference"],
    )