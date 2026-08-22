from datetime import datetime, timezone
from pathlib import Path
import json

from app.models import TraceEvent


class AuditLogger:
    def __init__(self, output_dir: str = "artifacts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.events: list[TraceEvent] = []

    def record(
        self,
        step: str,
        message: str,
        **data,
    ) -> None:
        event = TraceEvent(
            step=step,
            message=message,
            data=data,
        )

        self.events.append(event)

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        print(
            f"[{timestamp}] "
            f"[{step}] {message}"
        )

    def write_json(self) -> None:
        output = [
            {
                "step": event.step,
                "message": event.message,
                "data": event.data,
            }
            for event in self.events
        ]

        path = self.output_dir / "latest-run.json"

        path.write_text(
            json.dumps(output, indent=2),
            encoding="utf-8",
        )

    def write_markdown(self) -> None:
        lines = [
            "# TriagePilot Execution Trace",
            "",
            f"Generated: "
            f"{datetime.now(timezone.utc).isoformat()}",
            "",
        ]

        for index, event in enumerate(
            self.events,
            start=1,
        ):
            lines.extend([
                f"## {index}. {event.step}",
                "",
                event.message,
                "",
            ])

            if event.data:
                lines.extend([
                    "```json",
                    json.dumps(
                        event.data,
                        indent=2,
                    ),
                    "```",
                    "",
                ])

        path = self.output_dir / "latest-run.md"

        path.write_text(
            "\n".join(lines),
            encoding="utf-8",
        )

    def save(self) -> None:
        self.write_json()
        self.write_markdown()