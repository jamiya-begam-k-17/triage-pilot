from app.workflow import run_workflow


def main():
    results = run_workflow()

    print("\n=== TRIAGEPILOT SUMMARY ===")

    for result in results:
        print(
            f"{result.referral_id}: "
            f"{result.status.value}"
        )

    print(
        "\nDetailed trace: "
        "artifacts/latest-run.md"
    )


if __name__ == "__main__":
    main()