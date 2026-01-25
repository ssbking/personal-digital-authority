import hashlib
import json
from typing import Literal, TypedDict, Optional, Dict, Any
import uuid


# === DATA STRUCTURES ===

class AST(TypedDict):
    subject: Dict[str, str]
    verb: Dict[str, str]
    object: Dict[str, str]
    metadata: Dict[str, Any]


ErrorCode = Literal[
    "UNKNOWN_CAPABILITY",
    "UNSUPPORTED_ACTION",
    "INVALID_BINDING",
    "COMPILATION_FAILURE"
]


class CompilationError(TypedDict):
    error_code: ErrorCode
    message: str


class Constraints(TypedDict):
    scope: str
    reversible: bool
    sensitivity: Literal["LOW", "MEDIUM", "HIGH"]
    hrc_required: bool


class Provenance(TypedDict):
    ast_hash: str


class TaskManifest(TypedDict):
    task_id: str
    capability_id: str
    inputs: Dict[str, str]
    constraints: Constraints
    provenance: Provenance


class CompilationResult(TypedDict):
    status: Literal["SUCCESS", "FAILURE"]
    manifest: Optional[TaskManifest]
    error: Optional[CompilationError]


# === BLUEPRINT COMPILER IMPLEMENTATION ===

class BlueprintCompiler:
    """Deterministic AST to Task Manifest compiler."""
    
    # Static capability mapping table (closed-world)
    CAPABILITY_MAP = {
        "MUTATE:FILE:MOVE": "FILE_MOVE",
        "MUTATE:FILE:DELETE": "FILE_DELETE",
        "MUTATE:FILE:RENAME": "FILE_RENAME",
        "MUTATE:FOLDER:CREATE": "FOLDER_CREATE",
        "MUTATE:FOLDER:DELETE": "FOLDER_DELETE",
        "TRANSFORM:FILE:COMPRESS": "FILE_COMPRESS",
        "TRANSFORM:FILE:ENCRYPT": "FILE_ENCRYPT",
        "TRANSFORM:EMAIL:EXTRACT": "EMAIL_EXTRACT",
        "TRANSFORM:DATASET:FILTER": "DATASET_FILTER",
        "DISSEMINATE:FILE:COPY": "FILE_COPY",
        "DISSEMINATE:FILE:SHARE": "FILE_SHARE",
        "DISSEMINATE:EMAIL:SEND": "EMAIL_SEND",
        "DISSEMINATE:DEVICE:NOTIFY": "DEVICE_NOTIFY"
    }
    
    # UUID v5 namespace (deterministic)
    NAMESPACE_UUID = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
    
    def compile_ast(self, ast: AST) -> CompilationResult:
        """Convert AST to Task Manifest deterministically."""
        try:
            # 5.1 Capability Resolution
            capability_result = self._resolve_capability(ast)
            if capability_result["status"] == "FAILURE":
                return capability_result
            
            capability_id = capability_result["capability_id"]
            
            # 5.2 Input Binding
            inputs = self._bind_inputs(ast)
            
            # 5.3 Constraint Propagation
            constraints = self._propagate_constraints(ast)
            
            # 5.4 Manifest Construction
            # Generate deterministic task_id
            task_id = self._generate_task_id(ast)
            
            # Generate AST hash for provenance
            ast_hash = self._generate_ast_hash(ast)
            
            manifest: TaskManifest = {
                "task_id": task_id,
                "capability_id": capability_id,
                "inputs": inputs,
                "constraints": constraints,
                "provenance": {
                    "ast_hash": ast_hash
                }
            }
            
            return {
                "status": "SUCCESS",
                "manifest": manifest,
                "error": None
            }
            
        except Exception as e:
            return self._create_error(
                "COMPILATION_FAILURE",
                f"Compilation failed: {str(e)}"
            )
    
    def _resolve_capability(self, ast: AST) -> Dict[str, Any]:
        """Resolve capability from AST using static mapping table."""
        verb_class = ast["verb"]["class"]
        object_type = ast["object"]["type"]
        action = ast["verb"]["action"]
        
        key = f"{verb_class}:{object_type}:{action}"
        
        if key not in self.CAPABILITY_MAP:
            return {
                "status": "FAILURE",
                "capability_id": None,
                "error": self._create_error(
                    "UNKNOWN_CAPABILITY",
                    f"No capability found for: {key}"
                )
            }
        
        return {
            "status": "SUCCESS",
            "capability_id": self.CAPABILITY_MAP[key],
            "error": None
        }
    
    def _bind_inputs(self, ast: AST) -> Dict[str, str]:
        """Bind AST identifiers to manifest inputs."""
        inputs = {}
        
        # Subject identifier
        inputs["subject_identifier"] = ast["subject"]["identifier"]
        
        # Object identifier
        inputs["object_identifier"] = ast["object"]["identifier"]
        
        # Verb action (preserve exactly as provided)
        inputs["action"] = ast["verb"]["action"]
        
        # Additional metadata for context
        inputs["subject_type"] = ast["subject"]["type"]
        inputs["object_type"] = ast["object"]["type"]
        
        return inputs
    
    def _propagate_constraints(self, ast: AST) -> Constraints:
        """Propagate constraints from AST metadata verbatim."""
        metadata = ast["metadata"]
        
        constraints: Constraints = {
            "scope": metadata["scope"],
            "reversible": metadata["reversible"],
            "sensitivity": metadata["sensitivity"],
            "hrc_required": metadata["hrc_required"]
        }
        
        return constraints
    
    def _generate_task_id(self, ast: AST) -> str:
        """Generate deterministic task_id using UUID v5."""
        # Generate canonical AST JSON
        canonical_json = self._serialize_canonical_ast(ast)
        
        # Use UUID v5 with deterministic namespace
        return str(uuid.uuid5(self.NAMESPACE_UUID, canonical_json))
    
    def _generate_ast_hash(self, ast: AST) -> str:
        """Generate SHA-256 hash of canonical AST."""
        canonical_json = self._serialize_canonical_ast(ast)
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
    
    def _serialize_canonical_ast(self, ast: AST) -> str:
        """Serialize AST in canonical form for hashing."""
        # Create a copy to avoid modifying original
        ast_copy = {
            "subject": dict(ast["subject"]),
            "verb": dict(ast["verb"]),
            "object": dict(ast["object"]),
            "metadata": dict(ast["metadata"])
        }
        
        # Ensure all values are JSON serializable
        def prepare_for_json(obj):
            if isinstance(obj, dict):
                return {k: prepare_for_json(v) for k, v in sorted(obj.items())}
            elif isinstance(obj, list):
                return [prepare_for_json(v) for v in obj]
            else:
                return obj
        
        prepared = prepare_for_json(ast_copy)
        
        # Serialize with no whitespace, sorted keys
        return json.dumps(prepared, separators=(',', ':'), sort_keys=True)
    
    def _create_error(self, error_code: ErrorCode, message: str) -> CompilationResult:
        """Create standardized error response."""
        return {
            "status": "FAILURE",
            "manifest": None,
            "error": {
                "error_code": error_code,
                "message": message
            }
        }


# === PUBLIC INTERFACE ===

def compile_ast(ast: AST) -> CompilationResult:
    """Public pure function interface."""
    compiler = BlueprintCompiler()
    return compiler.compile_ast(ast)