import time
import json

from executors.navigation_executor import NavigationExecutor
from host.linux.bindings import LinuxHostBindings


def issue_fake_lease(task_id: str):
    return {
        "task_id": task_id,
        "issued_at": int(time.time()),
        "expires_at": int(time.time()) + 30,
        "signature": b"FAKE_SIGNATURE",
        "kernel_public_key": b"FAKE_KERNEL_PUBLIC_KEY",
    }


def main():
    host_adapter = LinuxHostBindings()
    executor = NavigationExecutor(host_adapter=host_adapter)

    manifest = {
        "task_id": "task-001",
        "capability_id": "NAVIGATE_URL",
        "inputs": {
            "target_type": "url",
            "target_id": "https://example.com",
            "navigation_mode": "foreground",
            "focus_policy": "FOREGROUND",
        },
    }

    lease = issue_fake_lease(manifest["task_id"])

    result = executor.execute(
        manifest=manifest,
        lease=lease,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
