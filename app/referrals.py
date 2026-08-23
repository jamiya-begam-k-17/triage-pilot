import json
from pathlib import Path

from app.models import Referral


DEFAULT_QUEUE_PATH = Path("challenge/referral-queue.json")


def load_referrals(
    path: str | Path = DEFAULT_QUEUE_PATH,
) -> list[Referral]:
    """
    Load referrals from the challenge referral queue.

    This module only loads input data. It does not make policy
    decisions or execute any casework actions.
    """

    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Referral queue not found: {file_path}"
        )

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "Referral queue must contain a JSON list."
        )

    referrals: list[Referral] = []

    for item in data:
        referrals.append(
            Referral(
                referral_id=item["referral_id"],
                received_at=item["received_at"],
                resident_ref=item["resident_ref"],
                source=item["source"],
                summary=item["summary"],
                requested_action=item["requested_action"],
                urgency=item["urgency"],
            )
        )

    return referrals