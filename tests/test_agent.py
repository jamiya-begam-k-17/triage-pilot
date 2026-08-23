from app.agent import TriageAgent
from app.models import (
    DecisionStatus,
    HistoryEvent,
    Referral,
    Resident,
)


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
    def __init__(self, resident):
        self.resident = resident

    def get_resident(self, resident_ref):
        return self.resident


def adult_resident():
    return Resident(
        resident_ref="R-TEST",
        status="Active",
        benefit_code="HS",
        district="North",
        award_monthly=1000.00,
        household=[
            {
                "name": "Adult Applicant",
                "date_of_birth": "1990-01-01",
                "relationship": "Applicant",
            }
        ],
        events=[
            HistoryEvent(
                date="2026-02-01",
                type="Review",
                detail="Award reviewed and unchanged.",
            ),
            HistoryEvent(
                date="2026-01-10",
                type="Evidence received",
                detail="Supporting evidence received.",
            ),
        ],
    )


def child_resident():
    return Resident(
        resident_ref="R-CHILD",
        status="Active",
        benefit_code="HS",
        district="North",
        award_monthly=1000.00,
        household=[
            {
                "name": "Adult Applicant",
                "date_of_birth": "1990-01-01",
                "relationship": "Applicant",
            },
            {
                "name": "Child",
                "date_of_birth": "2013-01-01",
                "relationship": "Son/daughter",
            },
        ],
        events=[
            HistoryEvent(
                date="2026-01-10",
                type="Review",
                detail="Household reviewed.",
            )
        ],
    )


def make_referral(
    requested_action,
    resident_ref="R-TEST",
):
    return Referral(
        referral_id="RF-TEST",
        received_at="2026-03-17T10:00:00",
        resident_ref=resident_ref,
        source="test",
        summary="Test referral",
        requested_action=requested_action,
        urgency="normal",
    )


def test_agent_completes_permitted_adult_case():
    resident = adult_resident()
    audit = FakeAudit()

    agent = TriageAgent(
        history_client=FakeHistoryClient(resident),
        audit=audit,
    )

    referral = make_referral(
        "Review household composition",
        resident.resident_ref,
    )

    result = agent.run(referral)

    assert result.status == DecisionStatus.COMPLETED
    assert result.intent == "Review household composition"
    assert result.action_taken == "Review household composition"


def test_agent_escalates_restricted_action():
    resident = adult_resident()
    audit = FakeAudit()

    agent = TriageAgent(
        history_client=FakeHistoryClient(resident),
        audit=audit,
    )

    referral = make_referral(
        "Update payment details",
        resident.resident_ref,
    )

    result = agent.run(referral)

    assert result.status == DecisionStatus.ESCALATED

    # The restricted action must never be performed.
    assert result.action_taken == "NONE"
    assert result.action_taken != referral.requested_action

    assert "approval" in result.reason.lower()


def test_agent_handoffs_child_household():
    resident = child_resident()
    audit = FakeAudit()

    agent = TriageAgent(
        history_client=FakeHistoryClient(resident),
        audit=audit,
    )

    referral = make_referral(
        "Draft triage note for supervisor",
        resident.resident_ref,
    )

    result = agent.run(referral)

    assert result.status == DecisionStatus.HANDOFF

    # ACA-2026/2 §3.9:
    # the triage note itself must not be drafted.
    assert result.action_taken == "NONE"
    assert result.action_taken != referral.requested_action

    assert "under 18" in result.reason.lower()


def test_agent_preserves_relevant_history():
    resident = adult_resident()
    audit = FakeAudit()

    agent = TriageAgent(
        history_client=FakeHistoryClient(resident),
        audit=audit,
    )

    referral = make_referral(
        "Review household composition",
        resident.resident_ref,
    )

    result = agent.run(referral)

    assert len(result.relevant_history) > 0

    # Do not assume a particular ordering unless history.py guarantees one.
    returned_dates = {
        event.date
        for event in result.relevant_history
    }

    assert "2026-01-10" in returned_dates
    assert "2026-02-01" in returned_dates


def test_agent_records_policy_decision():
    resident = adult_resident()
    audit = FakeAudit()

    agent = TriageAgent(
        history_client=FakeHistoryClient(resident),
        audit=audit,
    )

    referral = make_referral(
        "Update payment details",
        resident.resident_ref,
    )

    agent.run(referral)

    decide_events = [
        event
        for event in audit.events
        if event["step"] == "DECIDE"
    ]

    assert len(decide_events) == 1

    event = decide_events[0]

    assert event["data"]["policy_status"] == "REQUIRES_APPROVAL"
    assert event["data"]["policy_reference"] == "ACA-2026/1 §3.4"


def test_agent_does_not_execute_restricted_action():
    resident = adult_resident()
    audit = FakeAudit()

    agent = TriageAgent(
        history_client=FakeHistoryClient(resident),
        audit=audit,
    )

    referral = make_referral(
        "Suspend assistance",
        resident.resident_ref,
    )

    result = agent.run(referral)

    assert result.status == DecisionStatus.ESCALATED

    # Critical safety assertion:
    # the requested restricted action must never be executed.
    assert result.action_taken != "Suspend assistance"
    assert result.action_taken == "NONE"

    act_events = [
        event
        for event in audit.events
        if event["step"] == "ACT"
    ]

    assert len(act_events) == 1

    # The audit must explicitly record that nothing was taken.
    assert act_events[0]["data"]["action_taken"] == "NONE"

    assert "HARD STOP" in act_events[0]["message"]


if __name__ == "__main__":
    test_agent_completes_permitted_adult_case()
    test_agent_escalates_restricted_action()
    test_agent_handoffs_child_household()
    test_agent_preserves_relevant_history()
    test_agent_records_policy_decision()
    test_agent_does_not_execute_restricted_action()

    print("All agent tests passed.")