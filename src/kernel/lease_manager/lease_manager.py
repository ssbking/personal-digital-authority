import hashlib
import hmac
import json
from typing import Literal, TypedDict, Optional, Dict, Any


# === DATA STRUCTURES ===

class TaskManifest(TypedDict):
    task_id: str
    capability_id: str
    inputs: Dict[str, str]
    constraints: Dict[str, Any]
    provenance: Dict[str, str]


class TrustSnapshot(TypedDict):
    trust_score: float
    minimum_required: float


class HRCToken(TypedDict):
    confirmed: bool
    confirmed_at: int


class LeaseToken(TypedDict):
    task_id: str
    issued_at: int
    expires_at: int
    signature: str


class LeaseError(TypedDict):
    error_code: Literal[
        "INVALID_MANIFEST",
        "LEASE_EXPIRED",
        "INSUFFICIENT_TRUST",
        "HRC_REQUIRED",
        "LEASE_REVOKED"
    ]
    message: str


class LeaseDecision(TypedDict):
    status: Literal["GRANTED", "DENIED"]
    lease: Optional[LeaseToken]
    error: Optional[LeaseError]


# === LEASE MANAGER IMPLEMENTATION ===

class LeaseManager:
    """Deterministic lease evaluation and token issuance."""
    
    # System constants
    LEASE_DURATION = 300  # 5 minutes in seconds
    SECRET_KEY = b"lease_manager_secret_key_v1.0"  # In production, this would be configurable
    
    def evaluate_lease(
        self,
        manifest: TaskManifest,
        trust_snapshot: TrustSnapshot,
        now: int,
        hrc_token: Optional[HRCToken] = None
    ) -> LeaseDecision:
        """Evaluate lease for Task Manifest at specific time."""
        
        # 5.1 Manifest Integrity Check
        integrity_check = self._check_manifest_integrity(manifest)
        if integrity_check["status"] == "DENIED":
            return integrity_check
        
        # 5.2 Time Window Validation
        time_check = self._check_time_window(now)
        if time_check["status"] == "DENIED":
            return time_check
        
        # 5.3 Trust Threshold Validation
        trust_check = self._check_trust_threshold(trust_snapshot)
        if trust_check["status"] == "DENIED":
            return trust_check
        
        # 5.4 Hardware-Rooted Confirmation (HRC)
        hrc_check = self._check_hrc_requirement(manifest, hrc_token)
        if hrc_check["status"] == "DENIED":
            return hrc_check
        
        # 5.5 Lease Granting
        return self._grant_lease(manifest, now)
    
    def _check_manifest_integrity(self, manifest: TaskManifest) -> LeaseDecision:
        """Validate manifest contains required fields."""
        required_fields = ["task_id", "capability_id", "inputs", "constraints", "provenance"]
        
        for field in required_fields:
            if field not in manifest:
                return self._create_error(
                    "INVALID_MANIFEST",
                    f"Missing required field: {field}"
                )
        
        if not manifest["task_id"] or not isinstance(manifest["task_id"], str):
            return self._create_error(
                "INVALID_MANIFEST",
                "task_id must be a non-empty string"
            )
        
        # Validate hrc_required is boolean if present
        constraints = manifest.get("constraints", {})
        if "hrc_required" in constraints and not isinstance(constraints["hrc_required"], bool):
            return self._create_error(
                "INVALID_MANIFEST",
                "hrc_required must be boolean"
            )
        
        return {"status": "GRANTED", "lease": None, "error": None}
    
    def _check_time_window(self, now: int) -> LeaseDecision:
        """Validate current time is valid for lease evaluation."""
        if not isinstance(now, int):
            return self._create_error(
                "LEASE_EXPIRED",
                f"Current time must be integer, got {type(now)}"
            )
        
        if now < 0:
            return self._create_error(
                "LEASE_EXPIRED",
                f"Current time cannot be negative: {now}"
            )
        
        return {"status": "GRANTED", "lease": None, "error": None}
    
    def _check_trust_threshold(self, trust_snapshot: TrustSnapshot) -> LeaseDecision:
        """Validate trust score meets minimum requirement."""
        required_fields = ["trust_score", "minimum_required"]
        for field in required_fields:
            if field not in trust_snapshot:
                return self._create_error(
                    "INVALID_MANIFEST",
                    f"Missing trust snapshot field: {field}"
                )
        
        trust_score = trust_snapshot["trust_score"]
        minimum_required = trust_snapshot["minimum_required"]
        
        if not isinstance(trust_score, (int, float)):
            return self._create_error(
                "INSUFFICIENT_TRUST",
                f"Invalid trust score type: {type(trust_score)}"
            )
        
        if not isinstance(minimum_required, (int, float)):
            return self._create_error(
                "INSUFFICIENT_TRUST",
                f"Invalid minimum required type: {type(minimum_required)}"
            )
        
        if trust_score < minimum_required:
            return self._create_error(
                "INSUFFICIENT_TRUST",
                f"Trust score {trust_score} below minimum {minimum_required}"
            )
        
        return {"status": "GRANTED", "lease": None, "error": None}
    
    def _check_hrc_requirement(
        self,
        manifest: TaskManifest,
        hrc_token: Optional[HRCToken]
    ) -> LeaseDecision:
        """Enforce Hardware-Rooted Confirmation if required."""
        constraints = manifest.get("constraints", {})
        
        # HRC check only triggers when explicitly True
        if constraints.get("hrc_required") is True:
            if hrc_token is None:
                return self._create_error(
                    "HRC_REQUIRED",
                    "HRC token required but not provided"
                )
            
            if "confirmed" not in hrc_token:
                return self._create_error(
                    "HRC_REQUIRED",
                    "HRC token missing 'confirmed' field"
                )
            
            if not isinstance(hrc_token["confirmed"], bool):
                return self._create_error(
                    "HRC_REQUIRED",
                    "HRC token 'confirmed' field must be boolean"
                )
            
            if not hrc_token["confirmed"]:
                return self._create_error(
                    "HRC_REQUIRED",
                    "HRC token not confirmed"
                )
        
        return {"status": "GRANTED", "lease": None, "error": None}
    
    def _grant_lease(self, manifest: TaskManifest, now: int) -> LeaseDecision:
        """Issue a deterministic lease token."""
        task_id = manifest["task_id"]
        issued_at = now
        expires_at = now + self.LEASE_DURATION
        
        # Generate deterministic signature
        signature = self._generate_signature(task_id, issued_at, expires_at)
        
        lease: LeaseToken = {
            "task_id": task_id,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "signature": signature
        }
        
        return {
            "status": "GRANTED",
            "lease": lease,
            "error": None
        }
    
    def _generate_signature(self, task_id: str, issued_at: int, expires_at: int) -> str:
        """Generate deterministic HMAC-SHA256 signature."""
        # Concatenate components with delimiter
        message = f"{task_id}:{issued_at}:{expires_at}"
        
        # Generate HMAC-SHA256
        signature = hmac.new(
            self.SECRET_KEY,
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_lease(self, lease: LeaseToken, now: int) -> bool:
        """Verify a lease token is valid at given time."""
        try:
            # Verify signature
            expected_signature = self._generate_signature(
                lease["task_id"],
                lease["issued_at"],
                lease["expires_at"]
            )
            
            if lease["signature"] != expected_signature:
                return False
            
            # Verify not expired
            if now > lease["expires_at"]:
                return False
            
            # Verify issued_at <= now
            if lease["issued_at"] > now:
                return False
            
            return True
            
        except (KeyError, TypeError):
            return False
    
    def _create_error(self, error_code: Literal, message: str) -> LeaseDecision:
        """Create standardized error response."""
        return {
            "status": "DENIED",
            "lease": None,
            "error": {
                "error_code": error_code,
                "message": message
            }
        }


# === PUBLIC INTERFACE ===

def evaluate_lease(
    manifest: TaskManifest,
    trust_snapshot: TrustSnapshot,
    now: int,
    hrc_token: Optional[HRCToken] = None
) -> LeaseDecision:
    """Public pure function interface."""
    manager = LeaseManager()
    return manager.evaluate_lease(manifest, trust_snapshot, now, hrc_token)