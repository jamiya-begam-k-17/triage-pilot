"""
Manages the (pre-existing) resident history mock service that
TriageAgent's HistoryClient depends on.

This module does NOT reimplement or mock any resident data. It only
launches the repository's own `challenge/services/history_service.py`
as a subprocess if it is not already running, so that the real
backend (app.history.HistoryClient) has something to talk to.

No policy, triage, or referral logic lives here.
"""

from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HISTORY_SERVICE_SCRIPT = REPO_ROOT / "challenge" / "services" / "history_service.py"
HISTORY_SERVICE_URL = "http://127.0.0.1:8083"

_process: subprocess.Popen | None = None


def is_history_service_up(timeout: float = 1.0) -> bool:
    """Check the mock history service's own /health endpoint."""
    try:
        with urllib.request.urlopen(
            f"{HISTORY_SERVICE_URL}/health", timeout=timeout
        ) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def ensure_history_service_running(
    startup_wait_seconds: float = 5.0,
) -> tuple[bool, str]:
    """
    Ensure the resident history mock service is reachable.

    Returns (is_up, message). If the service is already running,
    nothing is launched. If not, this starts the repository's
    existing mock service script as a subprocess and waits briefly
    for it to come up.
    """
    global _process

    if is_history_service_up():
        return True, "Resident History service already running."

    if not HISTORY_SERVICE_SCRIPT.exists():
        return False, (
            f"History service script not found at "
            f"{HISTORY_SERVICE_SCRIPT}"
        )

    if _process is None or _process.poll() is not None:
        _process = subprocess.Popen(
            [sys.executable, str(HISTORY_SERVICE_SCRIPT), "--port", "8083"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    deadline = time.time() + startup_wait_seconds
    while time.time() < deadline:
        if is_history_service_up():
            return True, "Resident History service started."
        time.sleep(0.25)

    return False, (
        "Resident History service did not respond in time. "
        "It may need to be started manually: "
        f"python3 {HISTORY_SERVICE_SCRIPT} --port 8083"
    )
