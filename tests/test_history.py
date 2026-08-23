from app.history import HistoryClient, get_relevant_history


def main():
    client = HistoryClient()

    print("Testing health...")
    health = client.health()

    assert health["status"] == "ok"
    print(health)

    print("\nTesting resident...")
    resident = client.get_resident("R-20500")

    assert resident.resident_ref == "R-20500"

    print("Resident:", resident.resident_ref)
    print("Status:", resident.status)
    print("Award:", resident.award_monthly)
    print("Events:", len(resident.events))

    assert len(resident.events) > 0

    print("\nTesting relevant history...")

    class Referral:
        requested_action = "Review award"

    relevant = get_relevant_history(
        Referral(),
        resident,
    )

    assert relevant, "Expected at least one relevant history event."

    for event in relevant:
        print(
            f"- {event.date}: "
            f"{event.type} — {event.detail}"
        )

    print("\nHistory tests passed.")


if __name__ == "__main__":
    main()