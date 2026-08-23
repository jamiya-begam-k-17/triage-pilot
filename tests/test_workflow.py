from app.models import (
    AgentResult,
    DecisionStatus,
    Referral,
)

from app.workflow import run_workflow


class FakeAudit:
    def __init__(self):
        self.events = []

    def record(self, step, message, **data):
        self.events.append(
            {
                "step": step,
                "message": message,
                "data": data,
            }
        )

    def save(self):
        pass


class FakeHistoryClient:
    pass


class FakeAgent:
    def __init__(self, history_client, audit):
        self.history_client = history_client
        self.audit = audit

    def run(self, referral):
        return AgentResult(
            referral_id=referral.referral_id,
            resident_ref=referral.resident_ref,
            status=DecisionStatus.COMPLETED,
            intent=referral.requested_action,
            reason="Test completed.",
            action_taken=referral.requested_action,
        )


def make_referral(referral_id):
    return Referral(
        referral_id=referral_id,
        received_at="2026-03-17T10:00:00",
        resident_ref=f"R-{referral_id}",
        source="test",
        summary="Test referral.",
        requested_action="Review household composition",
        urgency="normal",
    )


def test_workflow_processes_all_referrals(monkeypatch):
    referrals = [
        make_referral("RF-001"),
        make_referral("RF-002"),
        make_referral("RF-003"),
    ]

    monkeypatch.setattr(
        "app.workflow.AuditLogger",
        FakeAudit,
    )

    monkeypatch.setattr(
        "app.workflow.HistoryClient",
        FakeHistoryClient,
    )

    monkeypatch.setattr(
        "app.workflow.load_referrals",
        lambda: referrals,
    )

    monkeypatch.setattr(
        "app.workflow.TriageAgent",
        FakeAgent,
    )

    results = run_workflow()

    assert len(results) == 3

    assert all(
        result.status == DecisionStatus.COMPLETED
        for result in results
    )


def test_workflow_does_not_stop_when_one_referral_fails(
    monkeypatch,
):
    referrals = [
        make_referral("RF-001"),
        make_referral("RF-002"),
        make_referral("RF-003"),
    ]

    class FailingAgent(FakeAgent):
        def run(self, referral):
            if referral.referral_id == "RF-002":
                raise RuntimeError(
                    "Simulated referral failure"
                )

            return super().run(referral)

    monkeypatch.setattr(
        "app.workflow.AuditLogger",
        FakeAudit,
    )

    monkeypatch.setattr(
        "app.workflow.HistoryClient",
        FakeHistoryClient,
    )

    monkeypatch.setattr(
        "app.workflow.load_referrals",
        lambda: referrals,
    )

    monkeypatch.setattr(
        "app.workflow.TriageAgent",
        FailingAgent,
    )

    results = run_workflow()

    assert len(results) == 3

    # First referral completed.
    assert results[0].status == DecisionStatus.COMPLETED

    # Second referral failed, but the workflow continued.
    assert results[1].status == DecisionStatus.FAILED
    assert results[1].action_taken == "NONE"

    # Third referral was still processed.
    assert results[2].status == DecisionStatus.COMPLETED

    assert "failed" in results[1].reason.lower()
