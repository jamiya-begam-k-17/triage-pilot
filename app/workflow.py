from app.agent import TriageAgent
from app.audit import AuditLogger
from app.history import HistoryClient
from app.models import AgentResult, DecisionStatus
from app.referrals import load_referrals


def run_workflow() -> list[AgentResult]:
    """
    Run the triage workflow for every referral.

    Safety properties:
    - One failed referral must never stop the remaining referrals.
    - Restricted actions are handled by TriageAgent/policy.
    - Failed referrals are explicitly marked FAILED.
    - No action is reported as completed when an exception occurs.
    """

    audit = AuditLogger()
    history_client = HistoryClient()

    referrals = load_referrals()

    audit.record(
        "RUN",
        f"Loaded {len(referrals)} referrals.",
        referral_count=len(referrals),
    )

    agent = TriageAgent(
        history_client=history_client,
        audit=audit,
    )

    results: list[AgentResult] = []

    for referral in referrals:
        try:
            result = agent.run(referral)
            results.append(result)

        except Exception as exc:
            # A single referral failure must not terminate
            # processing of the remaining referral queue.
            reason = f"Referral failed: {exc}"

            audit.record(
                "ERROR",
                "Referral failed without stopping the remaining run.",
                referral_id=referral.referral_id,
                error=str(exc),
                action_taken="NONE",
            )

            results.append(
                AgentResult(
                    referral_id=referral.referral_id,
                    resident_ref=referral.resident_ref,
                    status=DecisionStatus.FAILED,
                    intent=referral.requested_action,
                    reason=reason,
                    action_taken="NONE",
                    relevant_history=[],
                    missing_information=[],
                )
            )

    completed = sum(
        result.status == DecisionStatus.COMPLETED
        for result in results
    )

    escalated = sum(
        result.status == DecisionStatus.ESCALATED
        for result in results
    )

    handoff = sum(
        result.status == DecisionStatus.HANDOFF
        for result in results
    )

    failed = sum(
        result.status == DecisionStatus.FAILED
        for result in results
    )

    audit.record(
        "RUN",
        "Workflow completed.",
        total=len(results),
        completed=completed,
        escalated=escalated,
        handoff=handoff,
        failed=failed,
    )

    audit.save()

    return results