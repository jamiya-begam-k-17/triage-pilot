import json

from app.referrals import load_referrals


def test_load_referrals(tmp_path):
    queue_file = tmp_path / "referrals.json"

    data = [
        {
            "referral_id": "RF-TEST-001",
            "received_at": "2026-03-17T10:00:00",
            "resident_ref": "R-20500",
            "source": "overnight_queue",
            "summary": "Review household circumstances.",
            "requested_action": "Review household composition",
            "urgency": "normal",
        },
        {
            "referral_id": "RF-TEST-002",
            "received_at": "2026-03-17T11:00:00",
            "resident_ref": "R-20501",
            "source": "overnight_queue",
            "summary": "Update payment details.",
            "requested_action": "Update payment details",
            "urgency": "urgent",
        },
    ]

    queue_file.write_text(
        json.dumps(data),
        encoding="utf-8",
    )

    referrals = load_referrals(queue_file)

    assert len(referrals) == 2

    assert referrals[0].referral_id == "RF-TEST-001"
    assert referrals[0].resident_ref == "R-20500"
    assert referrals[0].requested_action == (
        "Review household composition"
    )

    assert referrals[1].referral_id == "RF-TEST-002"
    assert referrals[1].urgency == "urgent"


def test_load_referrals_rejects_non_list(tmp_path):
    queue_file = tmp_path / "invalid.json"

    queue_file.write_text(
        json.dumps({"referral_id": "RF-001"}),
        encoding="utf-8",
    )

    try:
        load_referrals(queue_file)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "JSON list" in str(exc)


def test_load_referrals_missing_file(tmp_path):
    missing_file = tmp_path / "missing.json"

    try:
        load_referrals(missing_file)
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass
