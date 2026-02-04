import sys
import time
import json

sys.path.append("src")

from executors.navigation_executor import NavigationExecutor
from host.linux.bindings import LinuxHostBindings
from host.types import LeaseVerificationResult


KERNEL_PUBLIC_KEY = "FAKE_KERNEL_PUBLIC_KEY"
EXECUTOR_PRIVATE_KEY = "FAKE_EXECUTOR_PRIVATE_KEY"


def issue_fake_lease(task_id: str):
    issued_at = int(time.time())
    expires_at = issued_at + 30

    return {
        "task_id": task_id,
        "issued_at": issued_at,
        "expires_at": expires_at,
        "signature": b"FAKE_SIGNATURE",
        "kernel_public_key": KERNEL_PUBLIC_KEY,
    }


def build_lease_payload(lease: dict) -> bytes:
    return f"{lease['task_id']}:{lease['issued_at']}:{lease['expires_at']}".encode()


def main():
    host = LinuxHostBindings()

    executor = NavigationExecutor(
        kernel_public_key=KERNEL_PUBLIC_KEY,
        executor_private_key=EXECUTOR_PRIVATE_KEY,
    )

    # ---- HOST BINDINGS (FINAL, SEMANTICALLY CORRECT) ----
    executor._verify_lease_signature = (
        lambda lease:
        host.verify_lease_signature(
            payload=build_lease_payload(lease),
            signature=lease.get("signature"),
            kernel_public_key=lease.get("kernel_public_key").encode(),
        )
        == LeaseVerificationResult.VERIFIED
    )

    executor._resolve_target = host.resolve_target

    executor._execute_navigate_url = (
        lambda target_id, navigation_mode, focus_policy:
        host.navigate("NAVIGATE_URL", target_id, navigation_mode, focus_policy).value.lower()
    )

    executor._execute_navigate_file = (
        lambda target_id, navigation_mode, focus_policy:
        host.navigate("NAVIGATE_FILE", target_id, navigation_mode, focus_policy).value.lower()
    )
    # ----------------------------------------------------

    manifest = {
        "task_id": "task-001",
        "capability_id": "NAVIGATE_URL",
        "inputs": {
            "target_type": "url",
            "target_id": "https://example.com",
            "navigation_mode": "foreground",
            "focus_policy": "steal",
        },
    }

    lease = issue_fake_lease(manifest["task_id"])

    result = executor.execute_task(
        manifest=manifest,
        lease=lease,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

