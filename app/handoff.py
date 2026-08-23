from app.audit import AuditLogger
from app.models import AgentResult, HistoryEvent, Referral, Resident


def create_handoff(
    referral: Referral,
    resident: Resident,
    relevant_history: list[HistoryEvent],
    reason: str,
) -> dict:
    """
    Build a caseworker handoff package.

    This does not make a decision or perform a restricted action.
    It packages information already retrieved by the agent.
    """

    package = {
        "referral_id": referral.referral_id,
        "resident_ref": referral.resident_ref,
        "urgency": referral.urgency,
        "requested_action": referral.requested_action,
        "referral_summary": referral.summary,
        "reason": reason,
        "resident": {
            "status": resident.status,
            "benefit_code": resident.benefit_code,
            "district": resident.district,
        },
        "household": resident.household,
        "relevant_history": [
            {
                "date": event.date,
                "type": event.type,
                "detail": event.detail,
            }
            for event in relevant_history
        ],
        "next_step": "Caseworker review required.",
    }

    return package