import unittest
import json
import uuid
from blueprint_compiler import compile_ast, BlueprintCompiler


class TestBlueprintCompiler(unittest.TestCase):
    
    def setUp(self):
        """Create a valid AST for testing."""
        self.valid_ast = {
            "subject": {
                "type": "USER",
                "identifier": "user123"
            },
            "verb": {
                "class": "MUTATE",
                "action": "move"
            },
            "object": {
                "type": "FILE",
                "identifier": "/docs/receipt.pdf"
            },
            "metadata": {
                "scope": "tax_2024",
                "reversible": True,
                "sensitivity": "MEDIUM",
                "hrc_required": False
            }
        }
    
    def test_successful_compilation(self):
        """Valid AST should produce a Task Manifest."""
        result = compile_ast(self.valid_ast)
        
        self.assertEqual(result["status"], "SUCCESS")
        self.assertIsNotNone(result["manifest"])
        
        manifest = result["manifest"]
        self.assertIsInstance(manifest["task_id"], str)
        self.assertEqual(manifest["capability_id"], "FILE_MOVE")
        
        # Verify inputs
        self.assertEqual(manifest["inputs"]["subject_identifier"], "user123")
        self.assertEqual(manifest["inputs"]["object_identifier"], "/docs/receipt.pdf")
        self.assertEqual(manifest["inputs"]["action"], "move")
        self.assertEqual(manifest["inputs"]["subject_type"], "USER")
        self.assertEqual(manifest["inputs"]["object_type"], "FILE")
        
        # Verify constraints propagated verbatim
        self.assertEqual(manifest["constraints"]["scope"], "tax_2024")
        self.assertEqual(manifest["constraints"]["reversible"], True)
        self.assertEqual(manifest["constraints"]["sensitivity"], "MEDIUM")
        self.assertEqual(manifest["constraints"]["hrc_required"], False)
        
        # Verify provenance
        self.assertIsInstance(manifest["provenance"]["ast_hash"], str)
        self.assertEqual(len(manifest["provenance"]["ast_hash"]), 64)  # SHA-256 hex length
    
    def test_deterministic_task_id(self):
        """Identical AST should produce identical task_id."""
        result1 = compile_ast(self.valid_ast)
        result2 = compile_ast(self.valid_ast)
        
        self.assertEqual(result1["status"], "SUCCESS")
        self.assertEqual(result2["status"], "SUCCESS")
        
        manifest1 = result1["manifest"]
        manifest2 = result2["manifest"]
        
        self.assertEqual(manifest1["task_id"], manifest2["task_id"])
        self.assertEqual(manifest1["provenance"]["ast_hash"], manifest2["provenance"]["ast_hash"])
    
    def test_deterministic_across_instances(self):
        """Different compiler instances should produce identical output."""
        compiler1 = BlueprintCompiler()
        compiler2 = BlueprintCompiler()
        
        result1 = compiler1.compile_ast(self.valid_ast)
        result2 = compiler2.compile_ast(self.valid_ast)
        
        self.assertEqual(
            json.dumps(result1, sort_keys=True),
            json.dumps(result2, sort_keys=True)
        )
    
    def test_unknown_capability(self):
        """Unknown capability should fail with UNKNOWN_CAPABILITY."""
        ast = self.valid_ast.copy()
        ast["verb"]["action"] = "unknown_action"
        
        result = compile_ast(ast)
        
        self.assertEqual(result["status"], "FAILURE")
        self.assertIsNone(result["manifest"])
        self.assertIsNotNone(result["error"])
        self.assertEqual(result["error"]["error_code"], "UNKNOWN_CAPABILITY")
    
    def test_unsupported_action(self):
        """Action not in mapping table should fail."""
        ast = self.valid_ast.copy()
        ast["verb"]["action"] = "invalid_action"
        
        result = compile_ast(ast)
        
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["error_code"], "UNKNOWN_CAPABILITY")
    
    def test_all_capability_mappings(self):
        """All defined capability mappings should work."""
        compiler = BlueprintCompiler()
        
        # Test all entries in the capability map
        for key, capability_id in compiler.CAPABILITY_MAP.items():
            verb_class, object_type, action = key.split(":")
            
            ast = {
                "subject": {"type": "USER", "identifier": "test"},
                "verb": {"class": verb_class, "action": action},
                "object": {"type": object_type, "identifier": "test_id"},
                "metadata": {
                    "scope": "test",
                    "reversible": True,
                    "sensitivity": "LOW",
                    "hrc_required": False
                }
            }
            
            result = compile_ast(ast)
            self.assertEqual(result["status"], "SUCCESS")
            self.assertEqual(result["manifest"]["capability_id"], capability_id)
    
    def test_constraint_propagation(self):
        """All constraints should be propagated verbatim."""
        test_cases = [
            {
                "reversible": False,
                "sensitivity": "HIGH",
                "hrc_required": True,
                "scope": "confidential"
            },
            {
                "reversible": True,
                "sensitivity": "LOW",
                "hrc_required": False,
                "scope": "public"
            }
        ]
        
        for metadata in test_cases:
            ast = self.valid_ast.copy()
            ast["metadata"] = metadata
            
            result = compile_ast(ast)
            self.assertEqual(result["status"], "SUCCESS")
            
            manifest = result["manifest"]
            constraints = manifest["constraints"]
            
            for key, value in metadata.items():
                self.assertEqual(constraints[key], value)
    
    def test_input_binding_preserves_identifiers(self):
        """Inputs should preserve identifiers exactly."""
        ast = {
            "subject": {"type": "SYSTEM", "identifier": "backup_service_01"},
            "verb": {"class": "TRANSFORM", "action": "compress"},
            "object": {"type": "FOLDER", "identifier": "/var/backups/2024"},
            "metadata": {
                "scope": "backup_operations",
                "reversible": True,
                "sensitivity": "LOW",
                "hrc_required": False
            }
        }
        
        result = compile_ast(ast)
        self.assertEqual(result["status"], "SUCCESS")
        
        inputs = result["manifest"]["inputs"]
        self.assertEqual(inputs["subject_identifier"], "backup_service_01")
        self.assertEqual(inputs["object_identifier"], "/var/backups/2024")
        self.assertEqual(inputs["action"], "compress")
        self.assertEqual(inputs["subject_type"], "SYSTEM")
        self.assertEqual(inputs["object_type"], "FOLDER")
    
    def test_no_mutation_of_input_ast(self):
        """Compiler should not mutate the input AST."""
        import copy
        
        original_ast = copy.deepcopy(self.valid_ast)
        ast_copy = copy.deepcopy(self.valid_ast)
        
        result = compile_ast(ast_copy)
        
        # Verify AST was not mutated
        self.assertEqual(ast_copy, original_ast)
        self.assertEqual(result["status"], "SUCCESS")
    
    def test_task_id_is_uuid_v5(self):
        """task_id should be a valid UUID v5."""
        result = compile_ast(self.valid_ast)
        
        self.assertEqual(result["status"], "SUCCESS")
        task_id = result["manifest"]["task_id"]
        
        # Parse as UUID to verify format
        parsed_uuid = uuid.UUID(task_id)
        self.assertEqual(parsed_uuid.version, 5)
    
    def test_canonical_serialization_determinism(self):
        """Canonical serialization should be deterministic."""
        compiler = BlueprintCompiler()
        
        # Create AST with different key order
        ast1 = {
            "subject": {"type": "USER", "identifier": "test"},
            "verb": {"class": "MUTATE", "action": "move"},
            "object": {"type": "FILE", "identifier": "test.txt"},
            "metadata": {
                "scope": "test",
                "reversible": True,
                "sensitivity": "LOW",
                "hrc_required": False
            }
        }
        
        # Same AST with different key order in metadata
        ast2 = {
            "metadata": {
                "hrc_required": False,
                "sensitivity": "LOW",
                "scope": "test",
                "reversible": True
            },
            "object": {"identifier": "test.txt", "type": "FILE"},
            "subject": {"identifier": "test", "type": "USER"},
            "verb": {"action": "move", "class": "MUTATE"}
        }
        
        # Both should produce identical canonical JSON
        json1 = compiler._serialize_canonical_ast(ast1)
        json2 = compiler._serialize_canonical_ast(ast2)
        
        self.assertEqual(json1, json2)
        
        # And therefore identical task_ids
        result1 = compile_ast(ast1)
        result2 = compile_ast(ast2)
        
        self.assertEqual(result1["manifest"]["task_id"], result2["manifest"]["task_id"])
    
    def test_compilation_failure_on_exception(self):
        """Exceptions during compilation should return COMPILATION_FAILURE."""
        compiler = BlueprintCompiler()
        
        # Create invalid AST that will cause an exception
        invalid_ast = {
            "subject": {"type": "USER", "identifier": "test"},
            "verb": {"class": "MUTATE", "action": "move"},
            "object": {"type": "FILE", "identifier": "test.txt"},
            "metadata": {
                "scope": "test",
                "reversible": "not_a_boolean",  # This will cause serialization error
                "sensitivity": "LOW",
                "hrc_required": False
            }
        }
        
        result = compiler.compile_ast(invalid_ast)
        
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["error"]["error_code"], "COMPILATION_FAILURE")
    
    def test_case_sensitive_action_mapping(self):
        """Action mapping should be case-sensitive."""
        # Test case-sensitive failure
        ast_lowercase = self.valid_ast.copy()
        ast_lowercase["verb"]["action"] = "move"  # lowercase
        
        ast_uppercase = self.valid_ast.copy()
        ast_uppercase["verb"]["action"] = "MOVE"  # uppercase
        
        result_lower = compile_ast(ast_lowercase)
        result_upper = compile_ast(ast_uppercase)
        
        # Lowercase should succeed (if in mapping)
        self.assertEqual(result_lower["status"], "SUCCESS")
        
        # Uppercase should fail because "MOVE" != "move" in mapping
        self.assertEqual(result_upper["status"], "FAILURE")
        self.assertEqual(result_upper["error"]["error_code"], "UNKNOWN_CAPABILITY")
    
    def test_action_preserved_verbatim_in_inputs(self):
        """Action should be preserved exactly in inputs."""
        test_cases = ["move", "MOVE", "Move", "MoVe", "DELETE", "delete"]
        
        for action in test_cases:
            ast = self.valid_ast.copy()
            ast["verb"]["action"] = action
            
            result = compile_ast(ast)
            
            if result["status"] == "SUCCESS":
                self.assertEqual(result["manifest"]["inputs"]["action"], action)


if __name__ == '__main__':
    unittest.main()