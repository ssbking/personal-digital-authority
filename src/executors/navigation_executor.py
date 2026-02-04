import json
import time
import hashlib
import hmac

class NavigationExecutor:
    SUPPORTED_CAPABILITIES = {"NAVIGATE_APP", "NAVIGATE_WINDOW", "NAVIGATE_URL", "NAVIGATE_FILE"}
    VALID_TARGET_TYPES = {"app", "window", "url", "file"}
    VALID_NAV_MODES = {"foreground", "background"}
    VALID_FOCUS_POLICIES = {"steal", "request", "none"}
    
    def __init__(self, kernel_public_key, executor_private_key):
        self.kernel_public_key = kernel_public_key
        self.executor_private_key = executor_private_key.encode()
    
    def _verify_lease_signature(self, lease):
        raise NotImplementedError("Lease signature verification must be provided by host")
    
    def _resolve_target(self, target_type, target_id):
        raise NotImplementedError("Target resolution must be provided by host")
    
    def _execute_navigate_app(self, target_id, navigation_mode, focus_policy):
        raise NotImplementedError("App navigation must be provided by host")
    
    def _execute_navigate_window(self, target_id, navigation_mode, focus_policy):
        raise NotImplementedError("Window navigation must be provided by host")
    
    def _execute_navigate_url(self, target_id, navigation_mode, focus_policy):
        raise NotImplementedError("URL navigation must be provided by host")
    
    def _execute_navigate_file(self, target_id, navigation_mode, focus_policy):
        raise NotImplementedError("File navigation must be provided by host")
    
    def _sign_result(self, result_data):
        canonical = json.dumps(result_data, sort_keys=True, separators=(',', ':'))
        signature = hmac.new(self.executor_private_key, canonical.encode(), hashlib.sha256).hexdigest()
        return signature
    
    def execute_task(self, manifest, lease):
        if not self._verify_lease_signature(lease):
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "INVALID_LEASE",
                    "message": ""
                }
            }
        
        if lease.get("task_id") != manifest.get("task_id"):
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "INVALID_LEASE",
                    "message": ""
                }
            }
        
        try:
            current_time = time.time()
            if current_time >= lease["expires_at"]:
                return {
                    "status": "FAILURE",
                    "error": {
                        "error_code": "LEASE_EXPIRED",
                        "message": ""
                    }
                }
        except (KeyError, TypeError):
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "INVALID_LEASE",
                    "message": ""
                }
            }
        
        capability_id = manifest.get("capability_id")
        if capability_id not in self.SUPPORTED_CAPABILITIES:
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "UNSUPPORTED_CAPABILITY",
                    "message": ""
                }
            }
        
        inputs = manifest.get("inputs", {})
        target_type = inputs.get("target_type")
        target_id = inputs.get("target_id")
        navigation_mode = inputs.get("navigation_mode")
        focus_policy = inputs.get("focus_policy")
        
        if not target_type or target_type not in self.VALID_TARGET_TYPES:
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "UNSUPPORTED_CAPABILITY",
                    "message": ""
                }
            }
        
        if capability_id == "NAVIGATE_APP" and target_type != "app":
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "EXECUTION_FAILED",
                    "message": ""
                }
            }
        if capability_id == "NAVIGATE_WINDOW" and target_type != "window":
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "EXECUTION_FAILED",
                    "message": ""
                }
            }
        if capability_id == "NAVIGATE_URL" and target_type != "url":
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "EXECUTION_FAILED",
                    "message": ""
                }
            }
        if capability_id == "NAVIGATE_FILE" and target_type != "file":
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "EXECUTION_FAILED",
                    "message": ""
                }
            }
        
        if not target_id or not isinstance(target_id, str) or not target_id.strip():
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "EXECUTION_FAILED",
                    "message": ""
                }
            }
        
        if not navigation_mode or navigation_mode not in self.VALID_NAV_MODES:
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "EXECUTION_FAILED",
                    "message": ""
                }
            }
        
        if not focus_policy or focus_policy not in self.VALID_FOCUS_POLICIES:
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "EXECUTION_FAILED",
                    "message": ""
                }
            }
        
        target_id = target_id.strip()
        
        try:
            resolution_result = self._resolve_target(target_type, target_id)
        except Exception:
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "EXECUTION_FAILED",
                    "message": ""
                }
            }
        
        if resolution_result == "TARGET_NOT_FOUND":
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "TARGET_NOT_FOUND",
                    "message": ""
                }
            }
        
        if resolution_result == "TARGET_NOT_ACCESSIBLE":
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "TARGET_NOT_ACCESSIBLE",
                    "message": ""
                }
            }
        
        if resolution_result != "RESOLVED":
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "EXECUTION_FAILED",
                    "message": ""
                }
            }
        
        try:
            if capability_id == "NAVIGATE_APP":
                nav_result = self._execute_navigate_app(target_id, navigation_mode, focus_policy)
            elif capability_id == "NAVIGATE_WINDOW":
                nav_result = self._execute_navigate_window(target_id, navigation_mode, focus_policy)
            elif capability_id == "NAVIGATE_URL":
                nav_result = self._execute_navigate_url(target_id, navigation_mode, focus_policy)
            elif capability_id == "NAVIGATE_FILE":
                nav_result = self._execute_navigate_file(target_id, navigation_mode, focus_policy)
            else:
                return {
                    "status": "FAILURE",
                    "error": {
                        "error_code": "EXECUTION_FAILED",
                        "message": ""
                    }
                }
        except Exception:
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "EXECUTION_FAILED",
                    "message": ""
                }
            }
        
        if nav_result == "NAVIGATION_BLOCKED":
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "NAVIGATION_BLOCKED",
                    "message": ""
                }
            }
        
        if nav_result not in {"success", "no_op"}:
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "EXECUTION_FAILED",
                    "message": ""
                }
            }
        
        output = {
            "task_id": manifest["task_id"],
            "capability_id": capability_id,
            "target_type": target_type,
            "target_id": target_id,
            "navigation_result": nav_result
        }
        
        result_to_sign = {
            "task_id": manifest["task_id"],
            "capability_id": capability_id,
            "status": "SUCCESS",
            "output": output
        }
        
        signature = self._sign_result(result_to_sign)
        
        return {
            "status": "SUCCESS",
            "output": output,
            "signature": signature
        }