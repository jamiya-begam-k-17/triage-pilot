from app.audit import AuditLogger
from app.history import (
    HistoryClient,
    get_relevant_history,
)
from app.models import (
    AgentResult,
    DecisionStatus,
    Referral,
)
from app.policy import (
    PolicyStatus,
    evaluate_action,
)


class TriageAgent:
    """
    Executes the three-step triage workflow:

        1. UNDERSTAND
        2. DECIDE
        3. ACT

    The agent never performs an action that the policy
    requires a supervisor to approve.
    """

    def __init__(
        self,
        history_client: HistoryClient,
        audit: AuditLogger,
    ):
        self.history_client = history_client
        self.audit = audit

    def run(
        self,
        referral: Referral,
    ) -> AgentResult:

        # -------------------------------------------------
        # STEP 1 — UNDERSTAND
        # -------------------------------------------------

        self.audit.record(
            "UNDERSTAND",
            f"Processing {referral.referral_id}",
            referral_id=referral.referral_id,
            resident_ref=referral.resident_ref,
            source=referral.source,
            urgency=referral.urgency,
            requested_action=referral.requested_action,
        )

        resident = self.history_client.get_resident(
            referral.resident_ref
        )

        relevant_history = get_relevant_history(
            referral,
            resident,
        )

        self.audit.record(
            "HISTORY",
            "Retrieved resident history and selected relevant events.",
            referral_id=referral.referral_id,
            total_events=len(resident.events),
            relevant_events=len(relevant_history),
            selected=[
                {
                    "date": event.date,
                    "type": event.type,
                    "detail": event.detail,
                }
                for event in relevant_history
            ],
        )

        intent = referral.requested_action

        self.audit.record(
            "UNDERSTAND",
            "Referral intent identified.",
            referral_id=referral.referral_id,
            intent=intent,
        )

        # -------------------------------------------------
        # STEP 2 — DECIDE
        # -------------------------------------------------

        policy_decision = evaluate_action(
            referral.requested_action
        )

        self.audit.record(
            "DECIDE",
            policy_decision.reason,
            referral_id=referral.referral_id,
            policy_status=policy_decision.status.value,
            policy_reference=policy_decision.policy_reference,
        )

        # -------------------------------------------------
        # STEP 3 — ACT
        # -------------------------------------------------

        if (
            policy_decision.status
            == PolicyStatus.REQUIRES_APPROVAL
        ):
            self.audit.record(
                "ACT",
                "HARD STOP: action blocked pending supervisor approval.",
                referral_id=referral.referral_id,
                requested_action=referral.requested_action,
                action_taken="NONE",
            )

            return AgentResult(
                referral_id=referral.referral_id,
                resident_ref=referral.resident_ref,
                status=DecisionStatus.REQUIRES_APPROVAL,
                intent=intent,
                reason=policy_decision.reason,
                action_taken="BLOCKED_PENDING_APPROVAL",
                relevant_history=relevant_history,
            )

        # At this stage the operation is permitted.
        self.audit.record(
            "ACT",
            "Permitted triage action completed.",
            referral_id=referral.referral_id,
            action_taken=referral.requested_action,
        )

        return AgentResult(
            referral_id=referral.referral_id,
            resident_ref=referral.resident_ref,
            status=DecisionStatus.COMPLETED,
            intent=intent,
            reason=policy_decision.reason,
            action_taken=referral.requested_action,
            relevant_history=relevant_history,
        )