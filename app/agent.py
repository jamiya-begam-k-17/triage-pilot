from app.handoff import create_handoff
from app.escalate import (
    CasePackageStore,
    build_case_package,
)
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
    Executes the triage workflow:

        1. UNDERSTAND
        2. DECIDE
        3. ACT

    Safety rules:

    - PERMITTED actions may be completed.
    - REQUIRES_APPROVAL actions are blocked.
    - HANDOFF cases are not acted upon.
    - Restricted actions are NEVER executed.
    - Child-household cases are NEVER drafted automatically.
    """

    def __init__(
        self,
        history_client: HistoryClient,
        audit: AuditLogger,
        case_package_store: CasePackageStore | None = None,
    ):
        self.history_client = history_client
        self.audit = audit
        self.case_package_store = (
            case_package_store or CasePackageStore()
        )

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
            referral.requested_action,
            household=resident.household,
            received_at=referral.received_at,
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

        # ---------------------------------------------
        # HARD STOP — SUPERVISOR APPROVAL REQUIRED
        # ---------------------------------------------

        if policy_decision.status == PolicyStatus.REQUIRES_APPROVAL:

            escalation_package = build_case_package(
                referral=referral,
                resident=resident,
                result=AgentResult(
                    referral_id=referral.referral_id,
                    resident_ref=referral.resident_ref,
                    status=DecisionStatus.ESCALATED,
                    intent=intent,
                    reason=policy_decision.reason,
                    action_taken="NONE",
                    relevant_history=relevant_history,
                ),
                policy_decision=policy_decision,
            )

            self.case_package_store.save(
                escalation_package
            )

            self.audit.record(
                "ACT",
                "HARD STOP: action blocked pending supervisor approval.",
                referral_id=referral.referral_id,
                requested_action=referral.requested_action,
                action_taken="NONE",
                escalation_destination="SUPERVISOR_QUEUE",
                escalation_package=escalation_package.__dict__,
            )

            return AgentResult(
                referral_id=referral.referral_id,
                resident_ref=referral.resident_ref,
                status=DecisionStatus.ESCALATED,
                intent=intent,
                reason=policy_decision.reason,
                action_taken="NONE",
                relevant_history=relevant_history,
                escalation_package=escalation_package.__dict__,
            )

        # ---------------------------------------------
        # HARD STOP — HUMAN HANDOFF REQUIRED
        # ---------------------------------------------

        if policy_decision.status == PolicyStatus.HANDOFF:

            handoff_package = create_handoff(
                referral=referral,
                resident=resident,
                relevant_history=relevant_history,
                reason=policy_decision.reason,
            )

            self.audit.record(
                "ACT",
                "HARD STOP: case handed off to caseworker.",
                referral_id=referral.referral_id,
                action_taken="NONE",
                handoff_destination="CASEWORKER_QUEUE",
                handoff_package=handoff_package,
            )

            return AgentResult(
                referral_id=referral.referral_id,
                resident_ref=referral.resident_ref,
                status=DecisionStatus.HANDOFF,
                intent=intent,
                reason=policy_decision.reason,
                action_taken="NONE",
                relevant_history=relevant_history,
                handoff_package=handoff_package,
            )

        # ---------------------------------------------
        # PERMITTED ACTION
        # ---------------------------------------------

        if policy_decision.status == PolicyStatus.PERMITTED:

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

        # ---------------------------------------------
        # DEFENSIVE FALLBACK
        # ---------------------------------------------

        self.audit.record(
            "ACT",
            "HARD STOP: unknown policy state.",
            referral_id=referral.referral_id,
            requested_action=referral.requested_action,
            action_taken="NONE",
        )

        return AgentResult(
            referral_id=referral.referral_id,
            resident_ref=referral.resident_ref,
            status=DecisionStatus.FAILED,
            intent=intent,
            reason="Unknown policy decision state.",
            action_taken="NONE",
            relevant_history=relevant_history,
        )