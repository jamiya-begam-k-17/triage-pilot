from app.policy import (
    PolicyStatus,
    evaluate_action,
)


def test_address_change_is_permitted():
    decision = evaluate_action(
        "Record change of address"
    )

    assert decision.status == PolicyStatus.PERMITTED


def test_household_review_is_permitted():
    decision = evaluate_action(
        "Review household composition"
    )

    assert decision.status == PolicyStatus.PERMITTED


def test_payment_details_require_approval():
    decision = evaluate_action(
        "Update payment details"
    )

    assert decision.status == PolicyStatus.REQUIRES_APPROVAL


def test_suspension_requires_approval():
    decision = evaluate_action(
        "Suspend assistance pending investigation"
    )

    assert decision.status == PolicyStatus.REQUIRES_APPROVAL


def test_unclear_action_defaults_to_approval():
    decision = evaluate_action(
        "Do something with the case"
    )

    assert decision.status == PolicyStatus.REQUIRES_APPROVAL


if __name__ == "__main__":
    test_address_change_is_permitted()
    test_household_review_is_permitted()
    test_payment_details_require_approval()
    test_suspension_requires_approval()
    test_unclear_action_defaults_to_approval()

    print("All policy tests passed.")