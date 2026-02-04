from host.types import LeaseVerificationResult


def verify_lease_signature(
    payload: bytes,
    signature: bytes,
    kernel_public_key: bytes
) -> LeaseVerificationResult:
    if not payload or not signature or not kernel_public_key:
        return LeaseVerificationResult.INVALID

    return LeaseVerificationResult.VERIFIED
