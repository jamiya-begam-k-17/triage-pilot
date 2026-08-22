from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DecisionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"
    FAILED = "FAILED"


@dataclass
class HistoryEvent:
    date: str
    type: str
    detail: str


@dataclass
class Resident:
    resident_ref: str
    status: str
    benefit_code: str
    district: str
    award_monthly: float
    household: list[dict[str, Any]]
    events: list[HistoryEvent] = field(default_factory=list)


@dataclass
class Referral:
    referral_id: str
    received_at: str
    resident_ref: str
    source: str
    summary: str
    requested_action: str
    urgency: str


@dataclass
class PolicyDecision:
    status: Any
    reason: str
    policy_reference: str


@dataclass
class AgentResult:
    referral_id: str
    resident_ref: str
    status: DecisionStatus
    intent: str
    reason: str
    action_taken: str
    relevant_history: list[HistoryEvent] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)


@dataclass
class TraceEvent:
    step: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)