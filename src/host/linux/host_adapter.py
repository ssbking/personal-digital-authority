from typing import Dict

from host.types import (
    TargetResolutionResult,
)

from .lease_verifier import verify_lease_signature
from .navigation_adapter import (
    navigate_url,
    navigate_file,
)


def get_host_capabilities() -> Dict:
    return {
        "platform": "linux",
        "adapter_version": "1.0",
        "navigation_types": ["url", "file"],
    }


def resolve_target(
    target_type: str,
    target_id: str
) -> TargetResolutionResult:
    if not isinstance(target_id, str) or not target_id:
        return TargetResolutionResult.INVALID_TARGET_FORMAT

    if target_type in ("url", "file"):
        return TargetResolutionResult.RESOLVED

    return TargetResolutionResult.TARGET_NOT_FOUND

