from app.policy import PolicyStatus, evaluate_action


REFERENCE_DATE = "2026-03-17T10:00:00"


def adult_household():
    return [
        {
            "name": "Adult Applicant",
            "date_of_birth": "1990-01-01",
            "relationship": "Applicant",
        }
    ]


def child_household():
    return [
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
    ]


# ---------------------------------------------------------------------------
# ACA-2026/1 §2 — permitted actions
# ---------------------------------------------------------------------------

def test_review_household_composition_is_permitted():
    decision = evaluate_action(
        "Review household composition",
        household=adult_household(),
        received_at=REFERENCE_DATE,
    )

    assert decision.status == PolicyStatus.PERMITTED
    assert decision.policy_reference == "ACA-2026/1 §2"


def test_flag_for_contact_attempt_is_permitted():
    decision = evaluate_action(
        "Flag for contact attempt",
        household=adult_household(),
        received_at=REFERENCE_DATE,
    )

    assert decision.status == PolicyStatus.PERMITTED
    assert decision.policy_reference == "ACA-2026/1 §2"


def test_draft_explanatory_note_is_permitted():
    decision = evaluate_action(
        "Draft explanatory note",
        household=adult_household(),
        received_at=REFERENCE_DATE,
    )

    assert decision.status == PolicyStatus.PERMITTED
    assert decision.policy_reference == "ACA-2026/1 §2"


def test_draft_triage_note_for_adult_household_is_permitted():
    decision = evaluate_action(
        "Draft triage note for supervisor",
        household=adult_household(),
        received_at=REFERENCE_DATE,
    )

    assert decision.status == PolicyStatus.PERMITTED
    assert decision.policy_reference == "ACA-2026/1 §2"


# ---------------------------------------------------------------------------
# ACA-2026/2 §3.9 / §5.2 — HANDOFF
# ---------------------------------------------------------------------------

def test_child_household_causes_handoff():
    decision = evaluate_action(
        "Draft triage note for supervisor",
        household=child_household(),
        received_at=REFERENCE_DATE,
    )

    assert decision.status == PolicyStatus.HANDOFF
    assert decision.policy_reference == "ACA-2026/2 §3.9"


def test_unknown_household_causes_handoff():
    decision = evaluate_action(
        "Draft triage note for supervisor",
        household=None,
        received_at=REFERENCE_DATE,
    )

    assert decision.status == PolicyStatus.HANDOFF
    assert decision.policy_reference == "ACA-2026/2 §5.2"


def test_missing_date_of_birth_causes_handoff():
    household = [
        {
            "name": "Applicant",
            "date_of_birth": None,
            "relationship": "Applicant",
        }
    ]

    decision = evaluate_action(
        "Draft triage note for supervisor",
        household=household,
        received_at=REFERENCE_DATE,
    )

    assert decision.status == PolicyStatus.HANDOFF
    assert decision.policy_reference == "ACA-2026/2 §5.2"


def test_invalid_date_of_birth_causes_handoff():
    household = [
        {
            "name": "Applicant",
            "date_of_birth": "not-a-date",
            "relationship": "Applicant",
        }
    ]

    decision = evaluate_action(
        "Draft triage note for supervisor",
        household=household,
        received_at=REFERENCE_DATE,
    )

    assert decision.status == PolicyStatus.HANDOFF
    assert decision.policy_reference == "ACA-2026/2 §5.2"


# ---------------------------------------------------------------------------
# ACA-2026/1 §3 — supervisor approval / escalation
# ---------------------------------------------------------------------------

def test_award_change_requires_approval():
    decision = evaluate_action(
        "Review award",
        household=adult_household(),
        received_at=REFERENCE_DATE,
    )

    assert decision.status == PolicyStatus.REQUIRES_APPROVAL
    assert decision.policy_reference == "ACA-2026/1 §3.1"


def test_payment_details_require_approval():
    decision = evaluate_action(
        "Update payment details",
        household=adult_household(),
        received_at=REFERENCE_DATE,
    )

    assert decision.status == PolicyStatus.REQUIRES_APPROVAL
    assert decision.policy_reference == "ACA-2026/1 §3.4"


def test_bank_details_require_approval():
    decision = evaluate_action(
        "Change bank details",
        household=adult_household(),
        received_at=REFERENCE_DATE,
    )

    assert decision.status == PolicyStatus.REQUIRES_APPROVAL
    assert decision.policy_reference == "ACA-2026/1 §3.4"


def test_card_details_require_approval():
    decision = evaluate_action(
        "Change card details",
        household=adult_household(),
        received_at=REFERENCE_DATE,
    )

    assert decision.status == PolicyStatus.REQUIRES_APPROVAL
    assert decision.policy_reference == "ACA-2026/1 §3.4"


def test_suspension_requires_approval():
    decision = evaluate_action(
        "Suspend assistance pending investigation",
        household=adult_household(),
        received_at=REFERENCE_DATE,
    )

    assert decision.status == PolicyStatus.REQUIRES_APPROVAL
    assert decision.policy_reference == "ACA-2026/1 §3.2"


def test_termination_requires_approval():
    decision = evaluate_action(
        "Terminate award",
        household=adult_household(),
        received_at=REFERENCE_DATE,
    )

    assert decision.status == PolicyStatus.REQUIRES_APPROVAL
    assert decision.policy_reference == "ACA-2026/1 §3.2"


def test_reinstatement_requires_approval():
    decision = evaluate_action(
        "Reinstate award",
        household=adult_household(),
        received_at=REFERENCE_DATE,
    )

    assert decision.status == PolicyStatus.REQUIRES_APPROVAL
    assert decision.policy_reference == "ACA-2026/1 §3.2"


def test_payment_change_requires_approval():
    decision = evaluate_action(
        "Change payment",
        household=adult_household(),
        received_at=REFERENCE_DATE,
    )

    assert decision.status == PolicyStatus.REQUIRES_APPROVAL
    assert decision.policy_reference == "ACA-2026/1 §3.3"


# ---------------------------------------------------------------------------
# ACA-2026/1 §6.1 — ambiguity defaults to approval
# ---------------------------------------------------------------------------

def test_unclear_action_defaults_to_approval():
    decision = evaluate_action(
        "Do something with the case",
        household=adult_household(),
        received_at=REFERENCE_DATE,
    )

    assert decision.status == PolicyStatus.REQUIRES_APPROVAL
    assert decision.policy_reference == "ACA-2026/1 §6.1"


def test_address_change_is_not_automatically_permitted():
    decision = evaluate_action(
        "Record change of address",
        household=adult_household(),
        received_at=REFERENCE_DATE,
    )

    assert decision.status == PolicyStatus.REQUIRES_APPROVAL
    assert decision.policy_reference == "ACA-2026/1 §6.1"


if __name__ == "__main__":
    test_review_household_composition_is_permitted()
    test_flag_for_contact_attempt_is_permitted()
    test_draft_explanatory_note_is_permitted()
    test_draft_triage_note_for_adult_household_is_permitted()

    test_child_household_causes_handoff()
    test_unknown_household_causes_handoff()
    test_missing_date_of_birth_causes_handoff()
    test_invalid_date_of_birth_causes_handoff()

    test_award_change_requires_approval()
    test_payment_details_require_approval()
    test_bank_details_require_approval()
    test_card_details_require_approval()
    test_suspension_requires_approval()
    test_termination_requires_approval()
    test_reinstatement_requires_approval()
    test_payment_change_requires_approval()

    test_unclear_action_defaults_to_approval()
    test_address_change_is_not_automatically_permitted()

    print("All policy tests passed.")