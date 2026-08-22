from dataclasses import dataclass
from enum import Enum


class PolicyStatus(str, Enum):
    PERMITTED = "PERMITTED"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"


@dataclass(frozen=True)
class PolicyDecision:
    status: PolicyStatus
    reason: str
    policy_reference: str


# These are derived directly from ACA-2026/1 section 3.
RESTRICTED_ACTION_RULES = (
    (
        "award",
        "ACA-2026/1 §3.1",
        "Changes to entitlement, award amount, or eligibility require supervisor approval.",
    ),
    (
        "suspend",
        "ACA-2026/1 §3.2",
        "Suspension, termination, or reinstatement of an award requires supervisor approval.",
    ),
    (
        "terminate",
        "ACA-2026/1 §3.2",
        "Suspension, termination, or reinstatement of an award requires supervisor approval.",
    ),
    (
        "reinstate",
        "ACA-2026/1 §3.2",
        "Suspension, termination, or reinstatement of an award requires supervisor approval.",
    ),
    (
        "payment",
        "ACA-2026/1 §3.3",
        "Initiation, alteration, or cancellation of a payment requires supervisor approval.",
    ),
    (
        "payment details",
        "ACA-2026/1 §3.4",
        "Changes to payment details require supervisor approval.",
    ),
    (
        "bank",
        "ACA-2026/1 §3.4",
        "Changes to bank details require supervisor approval.",
    ),
    (
        "card details",
        "ACA-2026/1 §3.4",
        "Changes to card details require supervisor approval.",
    ),
)


def evaluate_action(requested_action: str) -> PolicyDecision:
    """
    Evaluate whether a requested action may be performed autonomously.

    Policy ACA-2026/1 §6.1 requires unclear actions to be treated
    as requiring approval.
    """

    action = requested_action.strip().lower()

    for keyword, reference, reason in RESTRICTED_ACTION_RULES:
        if keyword in action:
            return PolicyDecision(
                status=PolicyStatus.REQUIRES_APPROVAL,
                reason=reason,
                policy_reference=reference,
            )

    # Explicitly permitted operations from section 2.
    permitted_actions = {
        "record change of address",
        "review household composition",
        "flag for contact attempt",
        "draft explanatory note",
        "draft triage note for supervisor",
    }

    if action in permitted_actions:
        return PolicyDecision(
            status=PolicyStatus.PERMITTED,
            reason="Action is permitted under ACA-2026/1 §2.",
            policy_reference="ACA-2026/1 §2",
        )

    # §6.1: ambiguity defaults to approval.
    return PolicyDecision(
        status=PolicyStatus.REQUIRES_APPROVAL,
        reason=(
            "Action could not be established as permitted. "
            "ACA-2026/1 §6.1 requires unclear actions to be treated "
            "as requiring approval."
        ),
        policy_reference="ACA-2026/1 §6.1",
    )