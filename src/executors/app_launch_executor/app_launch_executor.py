import hashlib

class AppLaunchExecutor:
    """Executor for application launch and URI opening actions."""
    
    SUPPORTED_CAPABILITIES = {"APP_LAUNCH", "APP_OPEN_URI"}
    
    def __init__(self, device_allowlist, app_allowlist, lease_public_key, executor_private_key):
        self.device_allowlist = device_allowlist
        self.app_allowlist = app_allowlist
        self.lease_public_key = lease_public_key
        self.executor_private_key = executor_private_key
        
    def _verify_lease_asymmetric(self, lease):
        if not isinstance(lease, dict):
            return False
        required = {"task_id", "current_time", "expires_at", "signature"}
        if not all(k in lease for k in required):
            return False
        if not isinstance(lease.get("current_time"), (int, float)):
            return False
        if not isinstance(lease.get("expires_at"), (int, float)):
            return False
        if lease["current_time"] >= lease["expires_at"]:
            return False
        data = f"{lease['task_id']}{lease['current_time']}{lease['expires_at']}".encode()
        expected_sig = f"SIGNED:{self.lease_public_key}:{hash(data)}"
        return lease.get("signature") == expected_sig
    
    def _sign_result_asymmetric(self, result):
        data = f"{result['output']['task_id']}{result['output']['capability_id']}{result['output']['app']}{result['output']['device']}{result['output']['status']}".encode()
        return f"SIGNED:{self.executor_private_key}:{hash(data)}"
    
    def execute_task(self, manifest, lease):
        if not self._verify_lease_asymmetric(lease):
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "INVALID_LEASE",
                    "message": "Lease verification failed"
                }
            }
        
        if lease.get("task_id") != manifest.get("task_id"):
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "INVALID_LEASE",
                    "message": "Lease task_id mismatch"
                }
            }
        
        capability_id = manifest.get("capability_id")
        if capability_id not in self.SUPPORTED_CAPABILITIES:
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "UNSUPPORTED_CAPABILITY",
                    "message": f"Unsupported capability: {capability_id}"
                }
            }
        
        inputs = manifest.get("inputs", {})
        app_identifier = inputs.get("app_identifier")
        target_device = inputs.get("target_device")
        
        if not app_identifier or not isinstance(app_identifier, str):
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "EXECUTION_FAILED",
                    "message": "Invalid app_identifier"
                }
            }
        
        if not target_device or not isinstance(target_device, str):
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "EXECUTION_FAILED",
                    "message": "Invalid target_device"
                }
            }
        
        if app_identifier not in self.app_allowlist:
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "EXECUTION_FAILED",
                    "message": f"Unknown app_identifier: {app_identifier}"
                }
            }
        
        if target_device not in self.device_allowlist:
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "EXECUTION_FAILED",
                    "message": f"Unknown target_device: {target_device}"
                }
            }
        
        if capability_id == "APP_OPEN_URI":
            uri = inputs.get("uri")
            if not uri or not isinstance(uri, str):
                return {
                    "status": "FAILURE",
                    "error": {
                        "error_code": "EXECUTION_FAILED",
                        "message": "Invalid uri for APP_OPEN_URI"
                    }
                }
        
        output = {
            "task_id": manifest.get("task_id"),
            "capability_id": capability_id,
            "app": app_identifier,
            "device": target_device,
            "status": "launched"
        }
        
        result = {
            "status": "SUCCESS",
            "output": output
        }
        
        result["signature"] = self._sign_result_asymmetric(result)
        return result