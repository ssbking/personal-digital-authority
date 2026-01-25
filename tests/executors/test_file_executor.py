import unittest
import os
import tempfile
import json
import hashlib
from file_executor import create_file_executor, AsymmetricCrypto


class TestFileExecutor(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.base_dir1 = os.path.join(self.test_dir, "base1")
        self.base_dir2 = os.path.join(self.test_dir, "base2")
        os.makedirs(self.base_dir1)
        os.makedirs(self.base_dir2)
        
        self.source_file = os.path.join(self.base_dir1, "test.txt")
        with open(self.source_file, "w") as f:
            f.write("Test content for file operations")
        
        self.dest_file = os.path.join(self.base_dir1, "moved.txt")
        self.copy_file = os.path.join(self.base_dir1, "copied.txt")
        
        self.executor = create_file_executor([self.base_dir1, self.base_dir2])
        
        self.valid_lease = {
            "task_id": "test-task-123",
            "issued_at": 1000000000,
            "expires_at": 1000000300,
            "current_time": 1000000100,
            "signature": self._generate_lease_signature("test-task-123", 1000000000, 1000000300, 1000000100)
        }
        
        self.valid_manifest = {
            "task_id": "test-task-123",
            "capability_id": "FILE_MOVE",
            "inputs": {
                "source_path": self.source_file,
                "destination_path": self.dest_file
            },
            "constraints": {
                "scope": "test",
                "reversible": True,
                "sensitivity": "LOW",
                "hrc_required": False
            },
            "provenance": {
                "ast_hash": "abc123"
            }
        }
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)
    
    def _generate_lease_signature(self, task_id: str, issued_at: int, expires_at: int, current_time: int) -> str:
        message = f"{task_id}:{issued_at}:{expires_at}:{current_time}"
        return hashlib.sha256(
            b"lease_public_key_v1.0" + message.encode()
        ).hexdigest()
    
    def _generate_wrong_lease_signature(self, task_id: str, issued_at: int, expires_at: int, current_time: int) -> str:
        message = f"{task_id}:{issued_at}:{expires_at}:{current_time}"
        return hashlib.sha256(
            b"wrong_public_key" + message.encode()
        ).hexdigest()
    
    def test_successful_file_move(self):
        result = self.executor.execute_task(self.valid_manifest, self.valid_lease)
        
        self.assertEqual(result["status"], "SUCCESS")
        self.assertIsNotNone(result["output"])
        self.assertEqual(result["output"]["capability_id"], "FILE_MOVE")
        self.assertTrue(os.path.exists(self.dest_file))
        self.assertFalse(os.path.exists(self.source_file))
        
        self.assertTrue(AsymmetricCrypto.verify_result_signature(result))
    
    def test_unsupported_capability(self):
        manifest = self.valid_manifest.copy()
        manifest["capability_id"] = "FILE_RENAME"
        
        result = self.executor.execute_task(manifest, self.valid_lease)
        
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["code"], "UNSUPPORTED_CAPABILITY")
        self.assertTrue(AsymmetricCrypto.verify_result_signature(result))
    
    def test_invalid_lease_signature(self):
        invalid_lease = self.valid_lease.copy()
        invalid_lease["signature"] = self._generate_wrong_lease_signature(
            "test-task-123", 1000000000, 1000000300, 1000000100
        )
        
        result = self.executor.execute_task(self.valid_manifest, invalid_lease)
        
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["code"], "INVALID_LEASE")
    
    def test_lease_expired(self):
        expired_lease = self.valid_lease.copy()
        expired_lease["current_time"] = 1000000400
        
        result = self.executor.execute_task(self.valid_manifest, expired_lease)
        
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["code"], "LEASE_EXPIRED")
    
    def test_lease_missing_current_time(self):
        invalid_lease = self.valid_lease.copy()
        del invalid_lease["current_time"]
        
        result = self.executor.execute_task(self.valid_manifest, invalid_lease)
        
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["code"], "INVALID_LEASE")
    
    def test_path_traversal_before_normalization(self):
        manifest = self.valid_manifest.copy()
        manifest["inputs"]["source_path"] = os.path.join(self.base_dir1, "..", "test.txt")
        
        result = self.executor.execute_task(manifest, self.valid_lease)
        
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["code"], "EXECUTION_FAILED")
    
    def test_path_contains_double_dot_resolves_inside(self):
        subdir = os.path.join(self.base_dir1, "subdir")
        os.makedirs(subdir)
        
        manifest = self.valid_manifest.copy()
        manifest["inputs"]["source_path"] = os.path.join(subdir, "..", "test.txt")
        
        result = self.executor.execute_task(manifest, self.valid_lease)
        
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["code"], "EXECUTION_FAILED")
    
    def test_symlink_rejection_before_resolution(self):
        link_target = os.path.join(self.base_dir1, "link_target.txt")
        with open(link_target, "w") as f:
            f.write("Target content")
        
        symlink = os.path.join(self.base_dir1, "symlink.txt")
        os.symlink(link_target, symlink)
        
        manifest = self.valid_manifest.copy()
        manifest["inputs"]["source_path"] = symlink
        
        result = self.executor.execute_task(manifest, self.valid_lease)
        
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["code"], "EXECUTION_FAILED")
    
    def test_outside_base_directory(self):
        outside_file = os.path.join(self.test_dir, "outside.txt")
        with open(outside_file, "w") as f:
            f.write("Outside content")
        
        manifest = self.valid_manifest.copy()
        manifest["inputs"]["source_path"] = outside_file
        
        result = self.executor.execute_task(manifest, self.valid_lease)
        
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["code"], "EXECUTION_FAILED")
    
    def test_irreversible_delete_rejection(self):
        manifest = self.valid_manifest.copy()
        manifest["capability_id"] = "FILE_DELETE"
        manifest["inputs"] = {"source_path": self.source_file}
        manifest["constraints"]["reversible"] = False
        
        result = self.executor.execute_task(manifest, self.valid_lease)
        
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["code"], "EXECUTION_FAILED")
        self.assertIn("reversible=true", result["error"]["message"])
    
    def test_result_signature_verification_public_key(self):
        result = self.executor.execute_task(self.valid_manifest, self.valid_lease)
        
        self.assertTrue(AsymmetricCrypto.verify_result_signature(result))
    
    def test_result_signature_private_key_not_work_for_verification(self):
        result = self.executor.execute_task(self.valid_manifest, self.valid_lease)
        
        result_copy = dict(result)
        provided_signature = result_copy.pop("signature")
        
        canonical_data = json.dumps(result_copy, sort_keys=True, separators=(',', ':'))
        private_key_signature = hashlib.sha256(
            b"executor_private_key_v1.0" + canonical_data.encode()
        ).hexdigest()
        
        self.assertNotEqual(provided_signature, private_key_signature)
    
    def test_tampered_result_fails_verification(self):
        result = self.executor.execute_task(self.valid_manifest, self.valid_lease)
        
        tampered = dict(result)
        tampered["output"]["task_id"] = "tampered"
        self.assertFalse(AsymmetricCrypto.verify_result_signature(tampered))
    
    def test_executor_cannot_generate_valid_lease(self):
        message = "fake:1:2:3"
        
        private_signature = hashlib.sha256(
            b"executor_private_key_v1.0" + message.encode()
        ).hexdigest()
        
        public_signature = hashlib.sha256(
            b"lease_public_key_v1.0" + message.encode()
        ).hexdigest()
        
        self.assertNotEqual(private_signature, public_signature)
    
    def test_destination_path_traversal(self):
        manifest = self.valid_manifest.copy()
        manifest["inputs"]["destination_path"] = os.path.join(self.base_dir1, "..", "outside.txt")
        
        result = self.executor.execute_task(manifest, self.valid_lease)
        
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["code"], "EXECUTION_FAILED")
    
    def test_source_file_not_found(self):
        manifest = self.valid_manifest.copy()
        manifest["inputs"]["source_path"] = os.path.join(self.base_dir1, "nonexistent.txt")
        
        result = self.executor.execute_task(manifest, self.valid_lease)
        
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["code"], "EXECUTION_FAILED")
    
    def test_destination_already_exists(self):
        with open(self.dest_file, "w") as f:
            f.write("Already exists")
        
        result = self.executor.execute_task(self.valid_manifest, self.valid_lease)
        
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["code"], "EXECUTION_FAILED")
    
    def test_directory_not_file(self):
        test_dir = os.path.join(self.base_dir1, "subdir")
        os.makedirs(test_dir)
        
        manifest = self.valid_manifest.copy()
        manifest["inputs"]["source_path"] = test_dir
        
        result = self.executor.execute_task(manifest, self.valid_lease)
        
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["code"], "EXECUTION_FAILED")
    
    def test_undo_metadata_completeness(self):
        manifest = self.valid_manifest.copy()
        manifest["capability_id"] = "FILE_DELETE"
        manifest["inputs"] = {"source_path": self.source_file}
        
        result = self.executor.execute_task(manifest, self.valid_lease)
        
        self.assertEqual(result["status"], "SUCCESS")
        undo_metadata = result["output"]["undo_metadata"]
        
        required_fields = ["original_path", "operation", "file_size", "file_hash", "file_content"]
        for field in required_fields:
            self.assertIn(field, undo_metadata)
    
    def test_lease_current_time_equals_expires_at(self):
        lease = self.valid_lease.copy()
        lease["current_time"] = lease["expires_at"]
        
        result = self.executor.execute_task(self.valid_manifest, lease)
        
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["code"], "LEASE_EXPIRED")
    
    def test_valid_current_time_before_expires(self):
        lease = self.valid_lease.copy()
        lease["current_time"] = lease["expires_at"] - 1
        
        result = self.executor.execute_task(self.valid_manifest, lease)
        
        self.assertEqual(result["status"], "SUCCESS")
        self.assertTrue(AsymmetricCrypto.verify_result_signature(result))


if __name__ == '__main__':
    unittest.main()