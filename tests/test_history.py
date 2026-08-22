from app.history import HistoryClient


def main():
    client = HistoryClient()

    print("Testing health...")
    print(client.health())

    print("\nTesting resident...")
    resident = client.get_resident("R-20500")

    print("Resident:", resident.resident_ref)
    print("Status:", resident.status)
    print("Award:", resident.award_monthly)
    print("Events:", len(resident.events))

    print("\nTesting relevant history...")

    # Minimal fake referral object for this test.
    class Referral:
        requested_action = "Review award"

    relevant = __import__(
        "app.history",
        fromlist=["get_relevant_history"],
    ).get_relevant_history(
        Referral(),
        resident,
    )

    for event in relevant:
        print(
            f"- {event.date}: "
            f"{event.type} — {event.detail}"
        )


if __name__ == "__main__":
    main()