import json
import unittest
from media_executor import MediaExecutor, ExecutionResult

def create_asymmetric_lease(lease_id, task_id, capability_id, current_time, expires_at, public_key):
    data = f"{lease_id}{task_id}{capability_id}{current_time}{expires_at}".encode()
    signature = f"SIGNED:{public_key}:{hash(data)}"
    return {
        "lease_id": lease_id,
        "task_id": task_id,
        "capability_id": capability_id,
        "current_time": current_time,
        "expires_at": expires_at,
        "signature": signature
    }

class ResourceExhausted(Exception):
    pass

class TestMediaExecutor(unittest.TestCase):
    def setUp(self):
        self.lease_public_key = "LEASE_PUBLIC_KEY_123"
        self.executor_private_key = "EXECUTOR_PRIVATE_KEY_456"
        self.device_allowlist = {"tv_living_room", "speakers_office"}
        self.executor = MediaExecutor(self.device_allowlist, self.lease_public_key, self.executor_private_key)
        
    def test_unsupported_capability(self):
        manifest = {"task_id": "t1", "capability_id": "MEDIA_DELETE", "inputs": {}}
        lease = create_asymmetric_lease("l1", "t1", "MEDIA_DELETE", 1000, 1100, self.lease_public_key)
        with self.assertRaises(ValueError) as cm:
            self.executor.execute_task(manifest, lease)
        self.assertIn("UNSUPPORTED_CAPABILITY", str(cm.exception))
        
    def test_invalid_lease_missing_fields(self):
        manifest = {"task_id": "t1", "capability_id": "MEDIA_PLAY", 
                   "inputs": {"media_uri": "file:///music.mp3", "target_device": "tv_living_room"}}
        lease = {"lease_id": "l1", "signature": "invalid"}
        with self.assertRaises(ValueError) as cm:
            self.executor.execute_task(manifest, lease)
        self.assertIn("INVALID_LEASE", str(cm.exception))
        
    def test_expired_lease(self):
        manifest = {"task_id": "t1", "capability_id": "MEDIA_PLAY", 
                   "inputs": {"media_uri": "file:///music.mp3", "target_device": "tv_living_room"}}
        lease = create_asymmetric_lease("l1", "t1", "MEDIA_PLAY", 1100, 1000, self.lease_public_key)
        with self.assertRaises(ValueError) as cm:
            self.executor.execute_task(manifest, lease)
        self.assertIn("INVALID_LEASE", str(cm.exception))
        
    def test_device_allowlist_enforcement(self):
        manifest = {"task_id": "t1", "capability_id": "MEDIA_PLAY", 
                   "inputs": {"media_uri": "file:///music.mp3", "target_device": "unknown_device"}}
        lease = create_asymmetric_lease("l1", "t1", "MEDIA_PLAY", 1000, 1100, self.lease_public_key)
        with self.assertRaises(ValueError) as cm:
            self.executor.execute_task(manifest, lease)
        self.assertIn("EXECUTION_FAILED", str(cm.exception))
        
    def test_media_play_success(self):
        manifest = {"task_id": "t1", "capability_id": "MEDIA_PLAY", 
                   "inputs": {"media_uri": "file:///music.mp3", "target_device": "tv_living_room"}}
        lease = create_asymmetric_lease("l1", "t1", "MEDIA_PLAY", 1000, 1100, self.lease_public_key)
        result = self.executor.execute_task(manifest, lease)
        self.assertEqual(result.capability_id, "MEDIA_PLAY")
        self.assertEqual(result.output["device"], "tv_living_room")
        self.assertEqual(result.output["status"], "applied")
        self.assertTrue(result.signature.startswith("SIGNED:"))
        
    def test_media_pause_success(self):
        manifest = {"task_id": "t1", "capability_id": "MEDIA_PAUSE", 
                   "inputs": {"media_uri": "file:///music.mp3", "target_device": "speakers_office"}}
        lease = create_asymmetric_lease("l1", "t1", "MEDIA_PAUSE", 1000, 1100, self.lease_public_key)
        result = self.executor.execute_task(manifest, lease)
        self.assertEqual(result.capability_id, "MEDIA_PAUSE")
        self.assertEqual(result.output["device"], "speakers_office")
        
    def test_media_stop_success(self):
        manifest = {"task_id": "t1", "capability_id": "MEDIA_STOP", 
                   "inputs": {"media_uri": "file:///music.mp3", "target_device": "tv_living_room"}}
        lease = create_asymmetric_lease("l1", "t1", "MEDIA_STOP", 1000, 1100, self.lease_public_key)
        result = self.executor.execute_task(manifest, lease)
        self.assertEqual(result.capability_id, "MEDIA_STOP")
        
    def test_media_seek_success(self):
        manifest = {"task_id": "t1", "capability_id": "MEDIA_SEEK", 
                   "inputs": {"media_uri": "file:///video.mp4", "target_device": "tv_living_room", 
                             "position_seconds": 120}}
        lease = create_asymmetric_lease("l1", "t1", "MEDIA_SEEK", 1000, 1100, self.lease_public_key)
        result = self.executor.execute_task(manifest, lease)
        self.assertEqual(result.capability_id, "MEDIA_SEEK")
        
    def test_media_seek_invalid_position(self):
        manifest = {"task_id": "t1", "capability_id": "MEDIA_SEEK", 
                   "inputs": {"media_uri": "file:///video.mp4", "target_device": "tv_living_room", 
                             "position_seconds": -1}}
        lease = create_asymmetric_lease("l1", "t1", "MEDIA_SEEK", 1000, 1100, self.lease_public_key)
        with self.assertRaises(ValueError) as cm:
            self.executor.execute_task(manifest, lease)
        self.assertIn("EXECUTION_FAILED", str(cm.exception))
        
    def test_idempotent_re_execution(self):
        manifest = {"task_id": "t1", "capability_id": "MEDIA_PLAY", 
                   "inputs": {"media_uri": "file:///music.mp3", "target_device": "tv_living_room"}}
        lease = create_asymmetric_lease("l1", "t1", "MEDIA_PLAY", 1000, 1100, self.lease_public_key)
        
        result1 = self.executor.execute_task(manifest, lease)
        result2 = self.executor.execute_task(manifest, lease)
        
        self.assertEqual(result1.task_id, result2.task_id)
        self.assertEqual(result1.capability_id, result2.capability_id)
        self.assertEqual(result1.output, result2.output)
        self.assertEqual(result1.signature, result2.signature)
        
    def test_result_signature_verification(self):
        manifest = {"task_id": "t1", "capability_id": "MEDIA_PLAY", 
                   "inputs": {"media_uri": "file:///music.mp3", "target_device": "tv_living_room"}}
        lease = create_asymmetric_lease("l1", "t1", "MEDIA_PLAY", 1000, 1100, self.lease_public_key)
        
        result = self.executor.execute_task(manifest, lease)
        
        data = f"{result.task_id}{result.capability_id}{json.dumps(result.output, sort_keys=True)}".encode()
        expected_signature = f"SIGNED:{self.executor_private_key}:{hash(data)}"
        
        self.assertEqual(result.signature, expected_signature)
        
    def test_simulate_resource_exhausted(self):
        class ExhaustedExecutor(MediaExecutor):
            def execute_task(self, manifest, lease):
                raise ResourceExhausted("RESOURCE_EXHAUSTED")
        
        exhausted_executor = ExhaustedExecutor(self.device_allowlist, self.lease_public_key, self.executor_private_key)
        manifest = {"task_id": "t1", "capability_id": "MEDIA_PLAY", 
                   "inputs": {"media_uri": "file:///music.mp3", "target_device": "tv_living_room"}}
        lease = create_asymmetric_lease("l1", "t1", "MEDIA_PLAY", 1000, 1100, self.lease_public_key)
        
        with self.assertRaises(ResourceExhausted) as cm:
            exhausted_executor.execute_task(manifest, lease)
        self.assertIn("RESOURCE_EXHAUSTED", str(cm.exception))
        
    def test_missing_inputs(self):
        manifest = {"task_id": "t1", "capability_id": "MEDIA_PLAY", "inputs": {}}
        lease = create_asymmetric_lease("l1", "t1", "MEDIA_PLAY", 1000, 1100, self.lease_public_key)
        with self.assertRaises(ValueError) as cm:
            self.executor.execute_task(manifest, lease)
        self.assertIn("EXECUTION_FAILED", str(cm.exception))
        
    def test_invalid_media_uri_type(self):
        manifest = {"task_id": "t1", "capability_id": "MEDIA_PLAY", 
                   "inputs": {"media_uri": 123, "target_device": "tv_living_room"}}
        lease = create_asymmetric_lease("l1", "t1", "MEDIA_PLAY", 1000, 1100, self.lease_public_key)
        with self.assertRaises(ValueError) as cm:
            self.executor.execute_task(manifest, lease)
        self.assertIn("EXECUTION_FAILED", str(cm.exception))
        
    def test_wrong_public_key_for_lease(self):
        manifest = {"task_id": "t1", "capability_id": "MEDIA_PLAY", 
                   "inputs": {"media_uri": "file:///music.mp3", "target_device": "tv_living_room"}}
        wrong_public_key = "WRONG_PUBLIC_KEY"
        lease = create_asymmetric_lease("l1", "t1", "MEDIA_PLAY", 1000, 1100, wrong_public_key)
        with self.assertRaises(ValueError) as cm:
            self.executor.execute_task(manifest, lease)
        self.assertIn("INVALID_LEASE", str(cm.exception))

if __name__ == "__main__":
    unittest.main()