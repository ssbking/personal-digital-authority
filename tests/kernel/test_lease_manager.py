import unittest
import time
from lease_manager import evaluate_lease, LeaseManager


class TestLeaseManager(unittest.TestCase):
    
    def setUp(self):
        """Create valid test data."""
        self.valid_manifest = {
            "task_id": "test-task-123",
            "capability_id": "FILE_MOVE",
            "inputs": {
                "subject_identifier": "user123",
                "object_identifier": "/docs/test.pdf",
                "action": "move"
            },
            "constraints": {
                "scope": "test",
                "reversible": True,
                "sensitivity": "MEDIUM",
                "hrc_required": False
            },
            "provenance": {
                "ast_hash": "abc123"
            }
        }
        
        self.valid_trust = {
            "trust_score": 0.8,
            "minimum_required": 0.5
        }
        
        self.now = int(time.time())
        
        self.hrc_token_confirmed = {
            "confirmed": True,
            "confirmed_at": self.now - 10
        }
        
        self.hrc_token_not_confirmed = {
            "confirmed": False,
            "confirmed_at": self.now - 10
        }
    
    def test_successful_lease_grant(self):
        """Valid inputs should grant lease."""
        result = evaluate_lease(
            self.valid_manifest,
            self.valid_trust,
            self.now
        )
        
        self.assertEqual(result["status"], "GRANTED")
        self.assertIsNotNone(result["lease"])
        self.assertIsNone(result["error"])
        
        lease = result["lease"]
        self.assertEqual(lease["task_id"], "test-task-123")
        self.assertEqual(lease["issued_at"], self.now)
        self.assertEqual(lease["expires_at"], self.now + 300)  # 5 minutes
        self.assertIsInstance(lease["signature"], str)
        self.assertEqual(len(lease["signature"]), 64)  # SHA-256 hex length
    
    def test_deterministic_grants(self):
        """Identical inputs should produce identical leases."""
        result1 = evaluate_lease(
            self.valid_manifest,
            self.valid_trust,
            self.now
        )
        
        result2 = evaluate_lease(
            self.valid_manifest,
            self.valid_trust,
            self.now
        )
        
        self.assertEqual(result1["status"], "GRANTED")
        self.assertEqual(result2["status"], "GRANTED")
        
        lease1 = result1["lease"]
        lease2 = result2["lease"]
        
        self.assertEqual(lease1["task_id"], lease2["task_id"])
        self.assertEqual(lease1["issued_at"], lease2["issued_at"])
        self.assertEqual(lease1["expires_at"], lease2["expires_at"])
        self.assertEqual(lease1["signature"], lease2["signature"])
    
    def test_missing_manifest_field(self):
        """Missing manifest field should deny with INVALID_MANIFEST."""
        manifest = self.valid_manifest.copy()
        del manifest["task_id"]
        
        result = evaluate_lease(
            manifest,
            self.valid_trust,
            self.now
        )
        
        self.assertEqual(result["status"], "DENIED")
        self.assertIsNone(result["lease"])
        self.assertIsNotNone(result["error"])
        self.assertEqual(result["error"]["error_code"], "INVALID_MANIFEST")
    
    def test_empty_task_id(self):
        """Empty task_id should deny with INVALID_MANIFEST."""
        manifest = self.valid_manifest.copy()
        manifest["task_id"] = ""
        
        result = evaluate_lease(
            manifest,
            self.valid_trust,
            self.now
        )
        
        self.assertEqual(result["status"], "DENIED")
        self.assertEqual(result["error"]["error_code"], "INVALID_MANIFEST")
    
    def test_insufficient_trust(self):
        """Trust score below minimum should deny."""
        low_trust = {
            "trust_score": 0.3,
            "minimum_required": 0.5
        }
        
        result = evaluate_lease(
            self.valid_manifest,
            low_trust,
            self.now
        )
        
        self.assertEqual(result["status"], "DENIED")
        self.assertEqual(result["error"]["error_code"], "INSUFFICIENT_TRUST")
    
    def test_exact_trust_threshold(self):
        """Trust score equal to minimum should grant."""
        exact_trust = {
            "trust_score": 0.5,
            "minimum_required": 0.5
        }
        
        result = evaluate_lease(
            self.valid_manifest,
            exact_trust,
            self.now
        )
        
        self.assertEqual(result["status"], "GRANTED")
    
    def test_missing_trust_field(self):
        """Missing trust field should deny."""
        incomplete_trust = {
            "trust_score": 0.8
            # missing minimum_required
        }
        
        result = evaluate_lease(
            self.valid_manifest,
            incomplete_trust,
            self.now
        )
        
        self.assertEqual(result["status"], "DENIED")
        self.assertEqual(result["error"]["error_code"], "INVALID_MANIFEST")
    
    def test_hrc_required_no_token(self):
        """HRC required with no token should deny."""
        manifest = self.valid_manifest.copy()
        manifest["constraints"]["hrc_required"] = True
        
        result = evaluate_lease(
            manifest,
            self.valid_trust,
            self.now
            # No HRC token provided
        )
        
        self.assertEqual(result["status"], "DENIED")
        self.assertEqual(result["error"]["error_code"], "HRC_REQUIRED")
    
    def test_hrc_required_not_confirmed(self):
        """HRC required with unconfirmed token should deny."""
        manifest = self.valid_manifest.copy()
        manifest["constraints"]["hrc_required"] = True
        
        result = evaluate_lease(
            manifest,
            self.valid_trust,
            self.now,
            self.hrc_token_not_confirmed
        )
        
        self.assertEqual(result["status"], "DENIED")
        self.assertEqual(result["error"]["error_code"], "HRC_REQUIRED")
    
    def test_hrc_required_confirmed(self):
        """HRC required with confirmed token should grant."""
        manifest = self.valid_manifest.copy()
        manifest["constraints"]["hrc_required"] = True
        
        result = evaluate_lease(
            manifest,
            self.valid_trust,
            self.now,
            self.hrc_token_confirmed
        )
        
        self.assertEqual(result["status"], "GRANTED")
    
    def test_hrc_not_required_with_token(self):
        """HRC not required but token provided should grant."""
        result = evaluate_lease(
            self.valid_manifest,
            self.valid_trust,
            self.now,
            self.hrc_token_confirmed
        )
        
        self.assertEqual(result["status"], "GRANTED")
    
    def test_hrc_token_missing_confirmed_field(self):
        """HRC token missing confirmed field should deny."""
        manifest = self.valid_manifest.copy()
        manifest["constraints"]["hrc_required"] = True
        
        invalid_hrc_token = {
            "confirmed_at": self.now  # missing confirmed field
        }
        
        result = evaluate_lease(
            manifest,
            self.valid_trust,
            self.now,
            invalid_hrc_token
        )
        
        self.assertEqual(result["status"], "DENIED")
        self.assertEqual(result["error"]["error_code"], "HRC_REQUIRED")
    
    def test_hrc_token_non_boolean_confirmed(self):
        """HRC token with non-boolean confirmed should deny."""
        manifest = self.valid_manifest.copy()
        manifest["constraints"]["hrc_required"] = True
        
        invalid_hrc_token = {
            "confirmed": "true",  # string instead of boolean
            "confirmed_at": self.now
        }
        
        result = evaluate_lease(
            manifest,
            self.valid_trust,
            self.now,
            invalid_hrc_token
        )
        
        self.assertEqual(result["status"], "DENIED")
        self.assertEqual(result["error"]["error_code"], "HRC_REQUIRED")
    
    def test_negative_time(self):
        """Negative now timestamp should deny."""
        result = evaluate_lease(
            self.valid_manifest,
            self.valid_trust,
            -1  # negative time
        )
        
        self.assertEqual(result["status"], "DENIED")
        self.assertEqual(result["error"]["error_code"], "LEASE_EXPIRED")
    
    def test_non_integer_time(self):
        """Non-integer now timestamp should deny."""
        result = evaluate_lease(
            self.valid_manifest,
            self.valid_trust,
            123.456  # float instead of int
        )
        
        self.assertEqual(result["status"], "DENIED")
        self.assertEqual(result["error"]["error_code"], "LEASE_EXPIRED")
    
    def test_lease_verification_valid(self):
        """Valid lease should verify correctly."""
        manager = LeaseManager()
        
        result = evaluate_lease(
            self.valid_manifest,
            self.valid_trust,
            self.now
        )
        
        lease = result["lease"]
        self.assertTrue(manager.verify_lease(lease, self.now))
    
    def test_lease_verification_expired(self):
        """Expired lease should fail verification."""
        manager = LeaseManager()
        
        past_time = self.now - 1000
        result = evaluate_lease(
            self.valid_manifest,
            self.valid_trust,
            past_time
        )
        
        lease = result["lease"]
        # Verify immediately should work
        self.assertTrue(manager.verify_lease(lease, past_time))
        
        # Verify after expiration should fail
        future_time = past_time + 1000  # After lease expiration
        self.assertFalse(manager.verify_lease(lease, future_time))
    
    def test_lease_verification_tampered(self):
        """Tampered lease should fail verification."""
        manager = LeaseManager()
        
        result = evaluate_lease(
            self.valid_manifest,
            self.valid_trust,
            self.now
        )
        
        lease = result["lease"].copy()
        lease["task_id"] = "tampered-task-id"  # Change task_id
        
        self.assertFalse(manager.verify_lease(lease, self.now))
    
    def test_lease_verification_invalid_signature(self):
        """Lease with invalid signature should fail verification."""
        manager = LeaseManager()
        
        result = evaluate_lease(
            self.valid_manifest,
            self.valid_trust,
            self.now
        )
        
        lease = result["lease"].copy()
        lease["signature"] = "invalid" + lease["signature"][6:]  # Modify signature
        
        self.assertFalse(manager.verify_lease(lease, self.now))
    
    def test_lease_verification_future_issued_at(self):
        """Lease with issued_at in future should fail verification."""
        manager = LeaseManager()
        
        future_time = self.now + 1000
        result = evaluate_lease(
            self.valid_manifest,
            self.valid_trust,
            future_time
        )
        
        lease = result["lease"]
        # Verify at time before issuance should fail
        self.assertFalse(manager.verify_lease(lease, self.now))
        
        # Verify at issuance time should work
        self.assertTrue(manager.verify_lease(lease, future_time))
    
    def test_deterministic_signature(self):
        """Signature generation should be deterministic."""
        manager = LeaseManager()
        
        task_id = "test-task"
        issued_at = 1234567890
        expires_at = 1234568190
        
        sig1 = manager._generate_signature(task_id, issued_at, expires_at)
        sig2 = manager._generate_signature(task_id, issued_at, expires_at)
        
        self.assertEqual(sig1, sig2)
        self.assertEqual(len(sig1), 64)  # SHA-256 hex length
    
    def test_fail_closed_behavior(self):
        """Any failure should result in DENIED status."""
        test_cases = [
            # (manifest_modification, trust_modification, hrc_token, expected_error)
            ({"task_id": ""}, {}, None, "INVALID_MANIFEST"),
            ({}, {"trust_score": 0.3}, None, "INSUFFICIENT_TRUST"),
            ({"constraints": {"hrc_required": True}}, {}, None, "HRC_REQUIRED"),
            ({"constraints": {"hrc_required": True}}, {}, {"confirmed": False}, "HRC_REQUIRED"),
        ]
        
        for manifest_mod, trust_mod, hrc_token, expected_error in test_cases:
            manifest = self.valid_manifest.copy()
            manifest.update(manifest_mod)
            
            trust = self.valid_trust.copy()
            trust.update(trust_mod)
            
            result = evaluate_lease(manifest, trust, self.now, hrc_token)
            
            self.assertEqual(result["status"], "DENIED")
            self.assertEqual(result["error"]["error_code"], expected_error)
    
    def test_non_boolean_hrc_required(self):
        """Non-boolean hrc_required should deny with INVALID_MANIFEST."""
        manifest = self.valid_manifest.copy()
        manifest["constraints"]["hrc_required"] = "true"  # String instead of boolean
        
        result = evaluate_lease(
            manifest,
            self.valid_trust,
            self.now
        )
        
        self.assertEqual(result["status"], "DENIED")
        self.assertEqual(result["error"]["error_code"], "INVALID_MANIFEST")
    
    def test_no_mutation_of_inputs(self):
        """Inputs should not be mutated."""
        import copy
        
        original_manifest = copy.deepcopy(self.valid_manifest)
        original_trust = copy.deepcopy(self.valid_trust)
        original_hrc = copy.deepcopy(self.hrc_token_confirmed)
        
        manifest_copy = copy.deepcopy(self.valid_manifest)
        trust_copy = copy.deepcopy(self.valid_trust)
        hrc_copy = copy.deepcopy(self.hrc_token_confirmed)
        
        result = evaluate_lease(
            manifest_copy,
            trust_copy,
            self.now,
            hrc_copy
        )
        
        self.assertEqual(manifest_copy, original_manifest)
        self.assertEqual(trust_copy, original_trust)
        self.assertEqual(hrc_copy, original_hrc)


if __name__ == '__main__':
    unittest.main()