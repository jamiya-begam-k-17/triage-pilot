from app.agent import TriageAgent
from app.audit import AuditLogger
from app.history import HistoryClient
from app.models import AgentResult, DecisionStatus
from app.referrals import load_referrals


def run_workflow() -> list[AgentResult]:
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
            audit.record(
                "ERROR",
                "Referral failed without stopping the remaining run.",
                referral_id=referral.referral_id,
                error=str(exc),
            )

            results.append(
                AgentResult(
                    referral_id=referral.referral_id,
                    resident_ref=referral.resident_ref,
                    status=DecisionStatus.FAILED,
                    intent=referral.requested_action,
                    reason=str(exc),
                    action_taken="NONE",
                )
            )

    completed = sum(
        result.status == DecisionStatus.COMPLETED
        for result in results
    )

    approval = sum(
        result.status == DecisionStatus.REQUIRES_APPROVAL
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
        requires_approval=approval,
        failed=failed,
    )

    audit.save()

    return results