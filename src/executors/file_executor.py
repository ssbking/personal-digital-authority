import os
import json
import hashlib
import shutil
from typing import Dict, Any, Optional, TypedDict, Literal


class TaskManifest(TypedDict):
    task_id: str
    capability_id: str
    inputs: Dict[str, str]
    constraints: Dict[str, Any]
    provenance: Dict[str, str]


class LeaseToken(TypedDict):
    task_id: str
    issued_at: int
    expires_at: int
    current_time: int
    signature: str


class ExecutionOutput(TypedDict):
    task_id: str
    capability_id: str
    result_summary: Dict[str, str]
    undo_metadata: Optional[Dict[str, Any]]


class ExecutionResult(TypedDict):
    status: Literal["SUCCESS", "FAILURE"]
    output: Optional[ExecutionOutput]
    error: Optional[Dict[str, str]]
    signature: str


ErrorCode = Literal[
    "UNSUPPORTED_CAPABILITY",
    "INVALID_LEASE",
    "LEASE_EXPIRED",
    "EXECUTION_FAILED",
    "RESOURCE_EXHAUSTED"
]


class AsymmetricCrypto:
    LEASE_PUBLIC_KEY = b"lease_public_key_v1.0"
    EXECUTOR_PRIVATE_KEY = b"executor_private_key_v1.0"
    EXECUTOR_PUBLIC_KEY = b"executor_public_key_v1.0"
    
    @staticmethod
    def verify_lease(lease: LeaseToken) -> bool:
        try:
            message = f"{lease['task_id']}:{lease['issued_at']}:{lease['expires_at']}:{lease['current_time']}"
            expected_signature = hashlib.sha256(
                AsymmetricCrypto.LEASE_PUBLIC_KEY + message.encode()
            ).hexdigest()
            return lease["signature"] == expected_signature
        except (KeyError, TypeError):
            return False
    
    @staticmethod
    def sign_result(result_data: Dict[str, Any]) -> str:
        canonical_data = json.dumps(result_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(
            AsymmetricCrypto.EXECUTOR_PRIVATE_KEY + canonical_data.encode()
        ).hexdigest()
    
    @staticmethod
    def verify_result_signature(result: ExecutionResult) -> bool:
        try:
            result_copy = dict(result)
            provided_signature = result_copy.pop("signature")
            canonical_data = json.dumps(result_copy, sort_keys=True, separators=(',', ':'))
            expected_signature = hashlib.sha256(
                AsymmetricCrypto.EXECUTOR_PUBLIC_KEY + canonical_data.encode()
            ).hexdigest()
            return provided_signature == expected_signature
        except (KeyError, TypeError, json.JSONDecodeError):
            return False


class FileExecutor:
    SUPPORTED_CAPABILITIES = {"FILE_MOVE", "FILE_COPY", "FILE_DELETE"}
    
    def __init__(self, base_directories: list[str]):
        self.base_directories = [os.path.realpath(b) for b in base_directories]
    
    def execute_task(self, manifest: TaskManifest, lease: LeaseToken) -> ExecutionResult:
        try:
            if not AsymmetricCrypto.verify_lease(lease):
                return self._create_error("INVALID_LEASE", "Lease signature verification failed")
            
            if "current_time" not in lease:
                return self._create_error("INVALID_LEASE", "Missing current_time in lease")
            
            if lease["current_time"] >= lease["expires_at"]:
                return self._create_error("LEASE_EXPIRED", "Lease has expired")
            
            if lease["task_id"] != manifest["task_id"]:
                return self._create_error("INVALID_LEASE", "Lease task_id mismatch")
            
            capability_id = manifest["capability_id"]
            if capability_id not in self.SUPPORTED_CAPABILITIES:
                return self._create_error(
                    "UNSUPPORTED_CAPABILITY",
                    f"Unsupported capability: {capability_id}"
                )
            
            validation_result = self._validate_and_normalize_paths(manifest)
            if validation_result["status"] == "FAILURE":
                return validation_result
            
            paths = validation_result["paths"]
            
            if capability_id == "FILE_MOVE":
                result = self._execute_file_move(manifest, paths)
            elif capability_id == "FILE_COPY":
                result = self._execute_file_copy(manifest, paths)
            elif capability_id == "FILE_DELETE":
                result = self._execute_file_delete(manifest, paths)
            else:
                return self._create_error("UNSUPPORTED_CAPABILITY", "Invalid capability")
            
            return result
            
        except Exception as e:
            return self._create_error("EXECUTION_FAILED", f"Execution error: {str(e)}")
    
    def _validate_and_normalize_paths(self, manifest: TaskManifest) -> Dict[str, Any]:
        try:
            inputs = manifest["inputs"]
            paths = {}
            
            if "source_path" not in inputs:
                return {"status": "FAILURE"}
            
            source_path_input = inputs["source_path"]
            
            if ".." in source_path_input:
                return {"status": "FAILURE"}
            
            source_path = os.path.realpath(source_path_input)
            
            if os.path.islink(source_path_input):
                return {"status": "FAILURE"}
            
            if not self._is_path_allowed(source_path):
                return {"status": "FAILURE"}
            
            if not os.path.exists(source_path):
                return {"status": "FAILURE"}
            
            if os.path.islink(source_path):
                return {"status": "FAILURE"}
            
            if not os.path.isfile(source_path):
                return {"status": "FAILURE"}
            
            paths["source_path"] = source_path
            
            capability_id = manifest["capability_id"]
            
            if capability_id in {"FILE_MOVE", "FILE_COPY"}:
                if "destination_path" not in inputs:
                    return {"status": "FAILURE"}
                
                dest_path_input = inputs["destination_path"]
                
                if ".." in dest_path_input:
                    return {"status": "FAILURE"}
                
                dest_path = os.path.realpath(dest_path_input)
                
                if os.path.islink(dest_path_input):
                    return {"status": "FAILURE"}
                
                if not self._is_path_allowed(dest_path):
                    return {"status": "FAILURE"}
                
                if os.path.exists(dest_path):
                    return {"status": "FAILURE"}
                
                if os.path.islink(dest_path):
                    return {"status": "FAILURE"}
                
                dest_dir = os.path.dirname(dest_path)
                if not os.path.exists(dest_dir):
                    return {"status": "FAILURE"}
                
                paths["destination_path"] = dest_path
            
            return {"status": "SUCCESS", "paths": paths}
            
        except (KeyError, TypeError, OSError):
            return {"status": "FAILURE"}
    
    def _is_path_allowed(self, resolved_path: str) -> bool:
        for base_dir in self.base_directories:
            try:
                common = os.path.commonpath([base_dir, resolved_path])
                if common == base_dir:
                    return True
            except ValueError:
                continue
        return False
    
    def _execute_file_move(self, manifest: TaskManifest, paths: Dict[str, str]) -> ExecutionResult:
        source = paths["source_path"]
        dest = paths["destination_path"]
        
        try:
            undo_metadata = {
                "original_path": source,
                "operation": "move",
                "destination": dest
            }
            
            file_size = os.path.getsize(source)
            shutil.move(source, dest)
            
            output: ExecutionOutput = {
                "task_id": manifest["task_id"],
                "capability_id": "FILE_MOVE",
                "result_summary": {
                    "source": source,
                    "destination": dest,
                    "operation": "move",
                    "size": str(file_size)
                },
                "undo_metadata": undo_metadata
            }
            
            return self._create_success_result(output)
            
        except Exception as e:
            return self._create_error("EXECUTION_FAILED", f"Move failed: {str(e)}")
    
    def _execute_file_copy(self, manifest: TaskManifest, paths: Dict[str, str]) -> ExecutionResult:
        source = paths["source_path"]
        dest = paths["destination_path"]
        
        try:
            file_size = os.path.getsize(source)
            shutil.copy2(source, dest)
            
            output: ExecutionOutput = {
                "task_id": manifest["task_id"],
                "capability_id": "FILE_COPY",
                "result_summary": {
                    "source": source,
                    "destination": dest,
                    "operation": "copy",
                    "size": str(file_size)
                },
                "undo_metadata": None
            }
            
            return self._create_success_result(output)
            
        except Exception as e:
            return self._create_error("EXECUTION_FAILED", f"Copy failed: {str(e)}")
    
    def _execute_file_delete(self, manifest: TaskManifest, paths: Dict[str, str]) -> ExecutionResult:
        source = paths["source_path"]
        
        if not manifest["constraints"].get("reversible", False):
            return self._create_error(
                "EXECUTION_FAILED",
                "FILE_DELETE requires reversible=true constraint"
            )
        
        try:
            with open(source, 'rb') as f:
                file_content = f.read()
            
            file_hash = hashlib.sha256(file_content).hexdigest()
            file_size = len(file_content)
            
            undo_metadata = {
                "original_path": source,
                "operation": "delete",
                "file_size": file_size,
                "file_hash": file_hash,
                "file_content": file_content.hex()
            }
            
            os.remove(source)
            
            output: ExecutionOutput = {
                "task_id": manifest["task_id"],
                "capability_id": "FILE_DELETE",
                "result_summary": {
                    "source": source,
                    "operation": "delete",
                    "size": str(file_size),
                    "hash": file_hash
                },
                "undo_metadata": undo_metadata
            }
            
            return self._create_success_result(output)
            
        except Exception as e:
            return self._create_error("EXECUTION_FAILED", f"Delete failed: {str(e)}")
    
    def _create_success_result(self, output: ExecutionOutput) -> ExecutionResult:
        result_data = {
            "status": "SUCCESS",
            "output": output,
            "error": None
        }
        
        signature = AsymmetricCrypto.sign_result(result_data)
        result_data["signature"] = signature
        
        return ExecutionResult(**result_data)
    
    def _create_error(self, error_code: ErrorCode, message: str) -> ExecutionResult:
        result_data = {
            "status": "FAILURE",
            "output": None,
            "error": {"code": error_code, "message": message}
        }
        
        signature = AsymmetricCrypto.sign_result(result_data)
        result_data["signature"] = signature
        
        return ExecutionResult(**result_data)


def create_file_executor(base_directories: list[str]) -> FileExecutor:
    return FileExecutor(base_directories)