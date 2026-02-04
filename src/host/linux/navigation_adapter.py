import os
import subprocess
from host.types import NavigationResult


def navigate_url(
    target_id: str,
    navigation_mode: str,
    focus_policy: str
) -> NavigationResult:
    if not isinstance(target_id, str) or not target_id:
        return NavigationResult.EXECUTION_FAILED

    if not target_id.startswith(("http://", "https://")):
        return NavigationResult.NAVIGATION_BLOCKED

    try:
        result = subprocess.run(
            ["xdg-open", target_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
    except Exception:
        return NavigationResult.EXECUTION_FAILED

    if result.returncode != 0:
        return NavigationResult.NAVIGATION_BLOCKED

    return NavigationResult.SUCCESS


def navigate_file(
    target_id: str,
    navigation_mode: str,
    focus_policy: str
) -> NavigationResult:
    if not isinstance(target_id, str) or not target_id:
        return NavigationResult.EXECUTION_FAILED

    if not os.path.exists(target_id):
        return NavigationResult.NAVIGATION_BLOCKED

    if not os.path.isfile(target_id):
        return NavigationResult.NAVIGATION_BLOCKED

    if not os.access(target_id, os.R_OK):
        return NavigationResult.NAVIGATION_BLOCKED

    try:
        result = subprocess.run(
            ["xdg-open", target_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
    except Exception:
        return NavigationResult.EXECUTION_FAILED

    if result.returncode != 0:
        return NavigationResult.NAVIGATION_BLOCKED

    return NavigationResult.SUCCESS

