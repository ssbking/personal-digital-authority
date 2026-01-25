import unittest
import json
from dsl_validator import validate_dsl


class TestDSLValidator(unittest.TestCase):
    
    def test_valid_complete_dsl(self):
        """Valid DSL should produce correct AST."""
        dsl = """SUBJECT(USER, user123)
VERB(MUTATE, move)
OBJECT(FILE, /docs/receipt.pdf)
META(tax_2024, true, MEDIUM, false)"""
        
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "VALID")
        self.assertIsNotNone(result["ast"])
        
        ast = result["ast"]
        self.assertEqual(ast["subject"]["type"], "USER")
        self.assertEqual(ast["subject"]["identifier"], "user123")
        self.assertEqual(ast["verb"]["class"], "MUTATE")
        self.assertEqual(ast["verb"]["action"], "move")
        self.assertEqual(ast["object"]["type"], "FILE")
        self.assertEqual(ast["object"]["identifier"], "/docs/receipt.pdf")
        self.assertEqual(ast["metadata"]["scope"], "tax_2024")
        self.assertEqual(ast["metadata"]["reversible"], True)
        self.assertEqual(ast["metadata"]["sensitivity"], "MEDIUM")
        self.assertEqual(ast["metadata"]["hrc_required"], False)
    
    def test_deterministic_identical_output(self):
        """Identical input must produce identical output."""
        dsl = """SUBJECT(SYSTEM, backup_service)
VERB(TRANSFORM, compress)
OBJECT(FOLDER, /backups)
META(daily_backup, false, LOW, false)"""
        
        result1 = validate_dsl(dsl)
        result2 = validate_dsl(dsl)
        
        self.assertEqual(json.dumps(result1, sort_keys=True), 
                        json.dumps(result2, sort_keys=True))
    
    def test_syntax_error_malformed(self):
        """Malformed syntax should produce SYNTAX_ERROR."""
        dsl = "SUBJECT(USER, test) VERB(MUTATE, move"
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["error"]["error_code"], "SYNTAX_ERROR")
    
    def test_syntax_error_extra_text(self):
        """Free text outside grammar should fail."""
        dsl = """SUBJECT(USER, test)
VERB(MUTATE, move)
OBJECT(FILE, test.txt)
META(scope, true, LOW, false)
extra text here"""
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["error"]["error_code"], "SYNTAX_ERROR")
    
    def test_missing_required_field(self):
        """Missing required token should fail."""
        dsl = """SUBJECT(USER, test)
VERB(MUTATE, move)
OBJECT(FILE, test.txt)"""
        # Missing META
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["error"]["error_code"], "MISSING_REQUIRED_FIELD")
    
    def test_unknown_subject_type(self):
        """Unknown subject type should fail."""
        dsl = """SUBJECT(INVALID_TYPE, test)
VERB(MUTATE, move)
OBJECT(FILE, test.txt)
META(scope, true, LOW, false)"""
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["error"]["error_code"], "UNKNOWN_SUBJECT_TYPE")
    
    def test_unknown_object_type(self):
        """Unknown object type should fail."""
        dsl = """SUBJECT(USER, test)
VERB(MUTATE, move)
OBJECT(INVALID_TYPE, test.txt)
META(scope, true, LOW, false)"""
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["error"]["error_code"], "UNKNOWN_OBJECT_TYPE")
    
    def test_unknown_verb_class(self):
        """Unknown verb class should fail."""
        dsl = """SUBJECT(USER, test)
VERB(INVALID_CLASS, move)
OBJECT(FILE, test.txt)
META(scope, true, LOW, false)"""
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["error"]["error_code"], "UNKNOWN_VERB_CLASS")
    
    def test_invalid_metadata_value_sensitivity(self):
        """Invalid sensitivity value should fail."""
        dsl = """SUBJECT(USER, test)
VERB(MUTATE, move)
OBJECT(FILE, test.txt)
META(scope, true, INVALID_SENSITIVITY, false)"""
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["error"]["error_code"], "INVALID_METADATA_VALUE")
    
    def test_invalid_metadata_value_boolean(self):
        """Invalid boolean value should fail at grammar level."""
        dsl = """SUBJECT(USER, test)
VERB(MUTATE, move)
OBJECT(FILE, test.txt)
META(scope, yes, LOW, false)"""
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["error"]["error_code"], "SYNTAX_ERROR")
    
    def test_ambiguous_scope_empty(self):
        """Empty scope should fail."""
        dsl = """SUBJECT(USER, test)
VERB(MUTATE, move)
OBJECT(FILE, test.txt)
META(, true, LOW, false)"""
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["error"]["error_code"], "AMBIGUOUS_SCOPE")
    
    def test_ambiguous_scope_invalid_chars(self):
        """Scope with invalid characters should fail."""
        dsl = """SUBJECT(USER, test)
VERB(MUTATE, move)
OBJECT(FILE, test.txt)
META(scope@invalid, true, LOW, false)"""
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["error"]["error_code"], "AMBIGUOUS_SCOPE")
    
    def test_hard_no_irreversible_deletion(self):
        """Irreversible deletion should fail."""
        dsl = """SUBJECT(USER, test)
VERB(MUTATE, delete)
OBJECT(FILE, test.txt)
META(scope, false, LOW, false)"""
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["error"]["error_code"], "HARD_NO_VIOLATION")
    
    def test_hard_no_financial_no_hrc(self):
        """High-sensitivity financial mutation without HRC should fail."""
        dsl = """SUBJECT(USER, test)
VERB(MUTATE, financial)
OBJECT(FILE, account.txt)
META(banking, true, HIGH, false)"""
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["error"]["error_code"], "HARD_NO_VIOLATION")
    
    def test_financial_with_hrc_allowed(self):
        """High-sensitivity financial mutation with HRC should pass."""
        dsl = """SUBJECT(USER, test)
VERB(MUTATE, financial)
OBJECT(FILE, account.txt)
META(banking, true, HIGH, true)"""
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "VALID")
    
    def test_reversible_deletion_allowed(self):
        """Reversible deletion should pass."""
        dsl = """SUBJECT(USER, test)
VERB(MUTATE, delete)
OBJECT(FILE, test.txt)
META(scope, true, LOW, false)"""
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "VALID")
    
    def test_all_verb_classes(self):
        """All verb classes should be accepted."""
        for verb_class in ["MUTATE", "TRANSFORM", "DISSEMINATE"]:
            dsl = f"""SUBJECT(USER, test)
VERB({verb_class}, action)
OBJECT(FILE, test.txt)
META(scope, true, LOW, false)"""
            result = validate_dsl(dsl)
            self.assertEqual(result["status"], "VALID", f"Failed for verb class: {verb_class}")
    
    def test_all_object_types(self):
        """All object types should be accepted."""
        for obj_type in ["FILE", "FOLDER", "EMAIL", "DATASET", "DEVICE"]:
            dsl = f"""SUBJECT(USER, test)
VERB(MUTATE, action)
OBJECT({obj_type}, identifier)
META(scope, true, LOW, false)"""
            result = validate_dsl(dsl)
            self.assertEqual(result["status"], "VALID", f"Failed for object type: {obj_type}")
    
    def test_all_sensitivity_levels(self):
        """All sensitivity levels should be accepted."""
        for sensitivity in ["LOW", "MEDIUM", "HIGH"]:
            dsl = f"""SUBJECT(USER, test)
VERB(MUTATE, action)
OBJECT(FILE, test.txt)
META(scope, true, {sensitivity}, false)"""
            result = validate_dsl(dsl)
            self.assertEqual(result["status"], "VALID", f"Failed for sensitivity: {sensitivity}")
    
    def test_duplicate_tokens(self):
        """Duplicate tokens should fail."""
        dsl = """SUBJECT(USER, test1)
SUBJECT(USER, test2)
VERB(MUTATE, move)
OBJECT(FILE, test.txt)
META(scope, true, LOW, false)"""
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["error"]["error_code"], "SYNTAX_ERROR")
    
    def test_whitespace_tolerance(self):
        """Whitespace should be ignored where allowed."""
        dsl = """  SUBJECT( USER  ,  user123  )  
VERB( MUTATE , move ) 
OBJECT( FILE , /docs/receipt.pdf )  
META( tax_2024 , true , MEDIUM , false )  """
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "VALID")
    
    def test_empty_input(self):
        """Empty input should fail."""
        result = validate_dsl("")
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["error"]["error_code"], "SYNTAX_ERROR")
    
    def test_whitespace_only_input(self):
        """Whitespace-only input should fail."""
        result = validate_dsl("   \n  \t  \n ")
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["error"]["error_code"], "SYNTAX_ERROR")
    
    def test_malformed_identifier(self):
        """Invalid identifier should fail."""
        dsl = """SUBJECT(USER, invalid@char)
VERB(MUTATE, move)
OBJECT(FILE, test.txt)
META(scope, true, LOW, false)"""
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "INVALID")
        # Should fail at grammar parsing stage
        self.assertEqual(result["error"]["error_code"], "SYNTAX_ERROR")
    
    def test_malformed_action(self):
        """Invalid action should fail."""
        dsl = """SUBJECT(USER, test)
VERB(MUTATE, invalid@action)
OBJECT(FILE, test.txt)
META(scope, true, LOW, false)"""
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["error"]["error_code"], "SYNTAX_ERROR")
    
    def test_credential_action_no_longer_fails(self):
        """Credential-related actions no longer fail Hard-No (heuristic removed)."""
        dsl = """SUBJECT(USER, test)
VERB(TRANSFORM, get_password)
OBJECT(FILE, config.ini)
META(scope, true, HIGH, true)"""
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "VALID")
    
    def test_financial_action_not_exact_match(self):
        """Only exact 'financial' action triggers Hard-No rule."""
        dsl = """SUBJECT(USER, test)
VERB(MUTATE, transfer_funds)
OBJECT(FILE, account.txt)
META(banking, true, HIGH, false)"""
        result = validate_dsl(dsl)
        self.assertEqual(result["status"], "VALID")


if __name__ == '__main__':
    unittest.main()