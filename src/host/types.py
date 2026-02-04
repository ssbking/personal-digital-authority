from enum import Enum

class LeaseVerificationResult(str, Enum):
    VERIFIED = "VERIFIED"
    INVALID = "INVALID"

class TargetResolutionResult(str, Enum):
    RESOLVED = "RESOLVED"
    TARGET_NOT_FOUND = "TARGET_NOT_FOUND"
    TARGET_NOT_ACCESSIBLE = "TARGET_NOT_ACCESSIBLE"
    INVALID_TARGET_FORMAT = "INVALID_TARGET_FORMAT"

class NavigationResult(str, Enum):
    SUCCESS = "SUCCESS"
    NO_OP = "NO_OP"
    NAVIGATION_BLOCKED = "NAVIGATION_BLOCKED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
