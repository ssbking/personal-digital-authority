from host.linux.host_adapter import (
    get_host_capabilities,
    resolve_target,
)
from host.linux.lease_verifier import verify_lease_signature
from host.linux.navigation_adapter import (
    navigate_url,
    navigate_file,
)


class LinuxHostBindings:
    def verify_lease_signature(self, payload, signature, kernel_public_key):
        return verify_lease_signature(payload, signature, kernel_public_key)

    def get_host_capabilities(self):
        return get_host_capabilities()

    def resolve_target(self, target_type, target_id):
        return resolve_target(target_type, target_id)

    def navigate(self, capability_id, target_id, navigation_mode, focus_policy):
        if capability_id == "NAVIGATE_URL":
            return navigate_url(target_id, navigation_mode, focus_policy)

        if capability_id == "NAVIGATE_FILE":
            return navigate_file(target_id, navigation_mode, focus_policy)

        return "EXECUTION_FAILED"
