import unittest
from app_launch_executor import AppLaunchExecutor

def create_asymmetric_lease(task_id, current_time, expires_at, public_key):
    data = f"{task_id}{current_time}{expires_at}".encode()
    signature = f"SIGNED:{public_key}:{hash(data)}"
    return {
        "task_id": task_id,
        "current_time": current_time,
        "expires_at": expires_at,
        "signature": signature
    }

class TestAppLaunchExecutor(unittest.TestCase):
    def setUp(self):
        self.device_allowlist = {"living_room_tv", "bedroom_tablet"}
        self.app_allowlist = {"maps", "music", "browser"}
        self.lease_public_key = "LEASE_PUBLIC_KEY_123"
        self.executor_private_key = "EXECUTOR_PRIVATE_KEY_456"
        self.executor = AppLaunchExecutor(
            self.device_allowlist,
            self.app_allowlist,
            self.lease_public_key,
            self.executor_private_key
        )
    
    def test_unsupported_capability(self):
        manifest = {
            "task_id": "t1",
            "capability_id": "APP_FOCUS",
            "inputs": {"app_identifier": "maps", "target_device": "living_room_tv"}
        }
        lease = create_asymmetric_lease("t1", 1000, 1100, self.lease_public_key)
        result = self.executor.execute_task(manifest, lease)
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["error_code"], "UNSUPPORTED_CAPABILITY")
    
    def test_invalid_lease_missing_fields(self):
        manifest = {
            "task_id": "t1",
            "capability_id": "APP_LAUNCH",
            "inputs": {"app_identifier": "maps", "target_device": "living_room_tv"}
        }
        lease = {"task_id": "t1"}
        result = self.executor.execute_task(manifest, lease)
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["error_code"], "INVALID_LEASE")
    
    def test_expired_lease(self):
        manifest = {
            "task_id": "t1",
            "capability_id": "APP_LAUNCH",
            "inputs": {"app_identifier": "maps", "target_device": "living_room_tv"}
        }
        lease = create_asymmetric_lease("t1", 1100, 1000, self.lease_public_key)
        result = self.executor.execute_task(manifest, lease)
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["error_code"], "INVALID_LEASE")
    
    def test_lease_task_id_mismatch(self):
        manifest = {
            "task_id": "t1",
            "capability_id": "APP_LAUNCH",
            "inputs": {"app_identifier": "maps", "target_device": "living_room_tv"}
        }
        lease = create_asymmetric_lease("t2", 1000, 1100, self.lease_public_key)
        result = self.executor.execute_task(manifest, lease)
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["error_code"], "INVALID_LEASE")
    
    def test_unknown_app_identifier(self):
        manifest = {
            "task_id": "t1",
            "capability_id": "APP_LAUNCH",
            "inputs": {"app_identifier": "unknown_app", "target_device": "living_room_tv"}
        }
        lease = create_asymmetric_lease("t1", 1000, 1100, self.lease_public_key)
        result = self.executor.execute_task(manifest, lease)
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["error_code"], "EXECUTION_FAILED")
    
    def test_unknown_target_device(self):
        manifest = {
            "task_id": "t1",
            "capability_id": "APP_LAUNCH",
            "inputs": {"app_identifier": "maps", "target_device": "unknown_device"}
        }
        lease = create_asymmetric_lease("t1", 1000, 1100, self.lease_public_key)
        result = self.executor.execute_task(manifest, lease)
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["error_code"], "EXECUTION_FAILED")
    
    def test_app_launch_success(self):
        manifest = {
            "task_id": "t1",
            "capability_id": "APP_LAUNCH",
            "inputs": {"app_identifier": "maps", "target_device": "living_room_tv"}
        }
        lease = create_asymmetric_lease("t1", 1000, 1100, self.lease_public_key)
        result = self.executor.execute_task(manifest, lease)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["output"]["app"], "maps")
        self.assertEqual(result["output"]["device"], "living_room_tv")
        self.assertEqual(result["output"]["status"], "launched")
        self.assertTrue("signature" in result)
        self.assertTrue(result["signature"].startswith("SIGNED:"))
    
    def test_app_open_uri_success(self):
        manifest = {
            "task_id": "t1",
            "capability_id": "APP_OPEN_URI",
            "inputs": {
                "app_identifier": "browser",
                "target_device": "bedroom_tablet",
                "uri": "https://example.com"
            }
        }
        lease = create_asymmetric_lease("t1", 1000, 1100, self.lease_public_key)
        result = self.executor.execute_task(manifest, lease)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["output"]["capability_id"], "APP_OPEN_URI")
        self.assertEqual(result["output"]["app"], "browser")
        self.assertEqual(result["output"]["device"], "bedroom_tablet")
    
    def test_app_open_uri_missing_uri(self):
        manifest = {
            "task_id": "t1",
            "capability_id": "APP_OPEN_URI",
            "inputs": {"app_identifier": "browser", "target_device": "bedroom_tablet"}
        }
        lease = create_asymmetric_lease("t1", 1000, 1100, self.lease_public_key)
        result = self.executor.execute_task(manifest, lease)
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["error_code"], "EXECUTION_FAILED")
    
    def test_result_signature_binding(self):
        manifest = {
            "task_id": "t1",
            "capability_id": "APP_LAUNCH",
            "inputs": {"app_identifier": "maps", "target_device": "living_room_tv"}
        }
        lease = create_asymmetric_lease("t1", 1000, 1100, self.lease_public_key)
        result = self.executor.execute_task(manifest, lease)
        self.assertTrue("signature" in result)
        self.assertTrue(result["signature"].startswith("SIGNED:"))
        self.assertIn(self.executor_private_key, result["signature"])
    
    def test_stateless_executor(self):
        manifest1 = {
            "task_id": "t1",
            "capability_id": "APP_LAUNCH",
            "inputs": {"app_identifier": "music", "target_device": "living_room_tv"}
        }
        manifest2 = {
            "task_id": "t1",
            "capability_id": "APP_LAUNCH",
            "inputs": {"app_identifier": "music", "target_device": "living_room_tv"}
        }
        lease = create_asymmetric_lease("t1", 1000, 1100, self.lease_public_key)
        
        result1 = self.executor.execute_task(manifest1, lease)
        result2 = self.executor.execute_task(manifest2, lease)
        
        self.assertEqual(result1["status"], "SUCCESS")
        self.assertEqual(result2["status"], "SUCCESS")
        self.assertEqual(result1["output"], result2["output"])
    
    def test_wrong_public_key_for_lease(self):
        manifest = {
            "task_id": "t1",
            "capability_id": "APP_LAUNCH",
            "inputs": {"app_identifier": "maps", "target_device": "living_room_tv"}
        }
        wrong_public_key = "WRONG_PUBLIC_KEY"
        lease = create_asymmetric_lease("t1", 1000, 1100, wrong_public_key)
        result = self.executor.execute_task(manifest, lease)
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["error_code"], "INVALID_LEASE")

if __name__ == "__main__":
    unittest.main()