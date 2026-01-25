import json
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ExecutionResult:
    task_id: str
    capability_id: str
    output: Dict[str, Any]
    signature: str

def verify_lease_asymmetric(lease: Dict[str, Any], public_key: str) -> bool:
    required = {"lease_id", "task_id", "capability_id", "current_time", "expires_at", "signature"}
    if not all(k in lease for k in required):
        return False
    if not isinstance(lease.get("current_time"), (int, float)):
        return False
    if not isinstance(lease.get("expires_at"), (int, float)):
        return False
    if lease["current_time"] >= lease["expires_at"]:
        return False
    data = f"{lease['lease_id']}{lease['task_id']}{lease['capability_id']}{lease['current_time']}{lease['expires_at']}".encode()
    calculated_signature = f"SIGNED:{public_key}:{hash(data)}"
    return lease.get("signature") == calculated_signature

def sign_result_asymmetric(task_id: str, capability_id: str, output: Dict[str, Any], private_key: str) -> str:
    data = f"{task_id}{capability_id}{json.dumps(output, sort_keys=True)}".encode()
    return f"SIGNED:{private_key}:{hash(data)}"

class MediaExecutor:
    SUPPORTED_CAPABILITIES = {"MEDIA_PLAY", "MEDIA_PAUSE", "MEDIA_STOP", "MEDIA_SEEK"}
    
    def __init__(self, device_allowlist: set, lease_public_key: str, executor_private_key: str):
        self.device_allowlist = device_allowlist
        self.lease_public_key = lease_public_key
        self.executor_private_key = executor_private_key
        
    def _check_device(self, target_device: str):
        if target_device not in self.device_allowlist:
            raise ValueError("EXECUTION_FAILED")
        
    def execute_task(self, manifest: Dict[str, Any], lease: Dict[str, Any]) -> ExecutionResult:
        if not verify_lease_asymmetric(lease, self.lease_public_key):
            raise ValueError("INVALID_LEASE")
        
        capability_id = manifest.get("capability_id")
        if capability_id not in self.SUPPORTED_CAPABILITIES:
            raise ValueError("UNSUPPORTED_CAPABILITY")
        
        inputs = manifest.get("inputs", {})
        media_uri = inputs.get("media_uri")
        target_device = inputs.get("target_device")
        
        if not media_uri or not isinstance(media_uri, str):
            raise ValueError("EXECUTION_FAILED")
        if not target_device or not isinstance(target_device, str):
            raise ValueError("EXECUTION_FAILED")
        
        self._check_device(target_device)
        
        if capability_id == "MEDIA_SEEK":
            position = inputs.get("position_seconds")
            if not isinstance(position, (int, float)) or position < 0:
                raise ValueError("EXECUTION_FAILED")
        
        output = {
            "task_id": manifest.get("task_id", ""),
            "capability_id": capability_id,
            "device": target_device,
            "status": "applied"
        }
        
        signature = sign_result_asymmetric(
            manifest.get("task_id", ""),
            capability_id,
            output,
            self.executor_private_key
        )
        
        return ExecutionResult(
            task_id=manifest.get("task_id", ""),
            capability_id=capability_id,
            output=output,
            signature=signature
        )