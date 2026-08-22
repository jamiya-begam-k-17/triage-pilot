import json
from pathlib import Path

from app.models import Referral


def load_referrals(
    path: str = "challenge/referral-queue.json",
) -> list[Referral]:
    file_path = Path(path)

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return [
        Referral(
            referral_id=item["referral_id"],
            received_at=item["received_at"],
            resident_ref=item["resident_ref"],
            source=item["source"],
            summary=item["summary"],
            requested_action=item["requested_action"],
            urgency=item["urgency"],
        )
        for item in data
    ]