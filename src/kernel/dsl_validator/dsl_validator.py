import re
import json
from typing import Literal, TypedDict, Optional, Union


# === DATA STRUCTURES (exactly as specified) ===

class SubjectNode(TypedDict):
    type: Literal["USER", "SYSTEM"]
    identifier: str


class ObjectNode(TypedDict):
    type: Literal["FILE", "FOLDER", "EMAIL", "DATASET", "DEVICE"]
    identifier: str


class VerbNode(TypedDict):
    class: Literal["MUTATE", "TRANSFORM", "DISSEMINATE"]
    action: str


class MetadataNode(TypedDict):
    scope: str
    reversible: bool
    sensitivity: Literal["LOW", "MEDIUM", "HIGH"]
    hrc_required: bool


class AST(TypedDict):
    subject: SubjectNode
    verb: VerbNode
    object: ObjectNode
    metadata: MetadataNode


class Location(TypedDict):
    line: Optional[int]
    column: Optional[int]


ErrorCode = Literal[
    "SYNTAX_ERROR",
    "UNKNOWN_SUBJECT_TYPE",
    "UNKNOWN_OBJECT_TYPE",
    "UNKNOWN_VERB_CLASS",
    "MISSING_REQUIRED_FIELD",
    "INVALID_METADATA_VALUE",
    "AMBIGUOUS_SCOPE",
    "HARD_NO_VIOLATION"
]


class ValidationError(TypedDict):
    error_code: ErrorCode
    message: str
    location: Location


class ValidationResult(TypedDict):
    status: Literal["VALID", "INVALID"]
    ast: Optional[AST]
    error: Optional[ValidationError]


# === VALIDATOR IMPLEMENTATION ===

class DSLValidator:
    """Pure, deterministic DSL validator with no side effects."""
    
    # Closed enums (exact matches from spec)
    SUBJECT_TYPES = {"USER", "SYSTEM"}
    OBJECT_TYPES = {"FILE", "FOLDER", "EMAIL", "DATASET", "DEVICE"}
    VERB_CLASSES = {"MUTATE", "TRANSFORM", "DISSEMINATE"}
    SENSITIVITY_VALUES = {"LOW", "MEDIUM", "HIGH"}
    
    # Grammar patterns (EBNF implementation - exactly as spec)
    IDENTIFIER_PATTERN = r'[A-Za-z0-9_\-/]+'
    ACTION_PATTERN = r'[A-Za-z0-9_\-]+'
    BOOLEAN_PATTERN = r'(true|false)'
    
    # Updated TOKEN_PATTERNS with exact EBNF matching
    TOKEN_PATTERNS = {
        "SUBJECT": rf'SUBJECT\s*\(\s*([A-Z]+)\s*,\s*({IDENTIFIER_PATTERN})\s*\)',
        "VERB": rf'VERB\s*\(\s*([A-Z]+)\s*,\s*({ACTION_PATTERN})\s*\)',
        "OBJECT": rf'OBJECT\s*\(\s*([A-Z]+)\s*,\s*({IDENTIFIER_PATTERN})\s*\)',
        "META": rf'META\s*\(\s*({IDENTIFIER_PATTERN})\s*,\s*({BOOLEAN_PATTERN})\s*,\s*([A-Z]+)\s*,\s*({BOOLEAN_PATTERN})\s*\)'
    }
    
    def validate_dsl(self, input_text: str) -> ValidationResult:
        """Main validation function - pure, deterministic, no side effects."""
        
        # Reject empty or whitespace-only input
        if not input_text or input_text.isspace():
            return self._create_error(
                "SYNTAX_ERROR",
                "Empty or whitespace-only input",
                {"line": None, "column": None}
            )
        
        # 5.1 Grammar parsing
        parse_result = self._parse_grammar(input_text)
        if parse_result["status"] == "INVALID":
            return parse_result
        
        tokens = parse_result["tokens"]
        
        # 5.2 Structural validation
        struct_result = self._validate_structure(tokens)
        if struct_result["status"] == "INVALID":
            return struct_result
        
        # Build AST components with validation
        ast_components = {}
        
        # Subject validation
        subject_result = self._validate_subject(tokens["SUBJECT"])
        if subject_result["status"] == "INVALID":
            return subject_result
        ast_components["subject"] = subject_result["ast_component"]
        
        # Verb validation
        verb_result = self._validate_verb(tokens["VERB"])
        if verb_result["status"] == "INVALID":
            return verb_result
        ast_components["verb"] = verb_result["ast_component"]
        
        # Object validation
        object_result = self._validate_object(tokens["OBJECT"])
        if object_result["status"] == "INVALID":
            return object_result
        ast_components["object"] = object_result["ast_component"]
        
        # Metadata validation
        meta_result = self._validate_metadata(tokens["META"])
        if meta_result["status"] == "INVALID":
            return meta_result
        ast_components["metadata"] = meta_result["ast_component"]
        
        # 5.5 Hard-No invariant validation
        hardno_result = self._validate_hard_no(ast_components)
        if hardno_result["status"] == "INVALID":
            return hardno_result
        
        # Success - return VALID with AST
        ast: AST = {
            "subject": ast_components["subject"],
            "verb": ast_components["verb"],
            "object": ast_components["object"],
            "metadata": ast_components["metadata"]
        }
        
        return {
            "status": "VALID",
            "ast": ast,
            "error": None
        }
    
    def _parse_grammar(self, text: str) -> dict:
        """Parse DSL text into tokens according to EBNF grammar."""
        lines = text.strip().split('\n')
        tokens = {}
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            matched = False
            for token_type, pattern in self.TOKEN_PATTERNS.items():
                match = re.fullmatch(pattern, line)
                if match:
                    if token_type in tokens:
                        return self._create_error(
                            "SYNTAX_ERROR",
                            f"Duplicate {token_type} declaration",
                            {"line": i+1, "column": 1}
                        )
                    tokens[token_type] = {
                        "raw": line,
                        "values": match.groups(),
                        "line": i+1,
                        "column": 1
                    }
                    matched = True
                    break
            
            if not matched:
                return self._create_error(
                    "SYNTAX_ERROR",
                    f"Invalid syntax at line {i+1}",
                    {"line": i+1, "column": 1}
                )
        
        return {"status": "VALID", "tokens": tokens}
    
    def _validate_structure(self, tokens: dict) -> dict:
        """Validate exactly one of each required token exists."""
        required = {"SUBJECT", "VERB", "OBJECT", "META"}
        for req in required:
            if req not in tokens:
                return self._create_error(
                    "MISSING_REQUIRED_FIELD",
                    f"Missing required {req} declaration",
                    None
                )
        
        # Check no extra tokens
        if len(tokens) > 4:
            return self._create_error(
                "SYNTAX_ERROR",
                "Extra declarations beyond required tokens",
                None
            )
        
        return {"status": "VALID"}
    
    def _validate_subject(self, token: dict) -> dict:
        """Validate SUBJECT token and create SubjectNode."""
        subj_type, identifier = token["values"]
        
        if subj_type not in self.SUBJECT_TYPES:
            return self._create_error(
                "UNKNOWN_SUBJECT_TYPE",
                f"Unknown subject type: {subj_type}",
                token
            )
        
        return {
            "status": "VALID",
            "ast_component": {
                "type": subj_type,
                "identifier": identifier
            }
        }
    
    def _validate_verb(self, token: dict) -> dict:
        """Validate VERB token and create VerbNode."""
        verb_class, action = token["values"]
        
        if verb_class not in self.VERB_CLASSES:
            return self._create_error(
                "UNKNOWN_VERB_CLASS",
                f"Unknown verb class: {verb_class}",
                token
            )
        
        return {
            "status": "VALID",
            "ast_component": {
                "class": verb_class,
                "action": action
            }
        }
    
    def _validate_object(self, token: dict) -> dict:
        """Validate OBJECT token and create ObjectNode."""
        obj_type, identifier = token["values"]
        
        if obj_type not in self.OBJECT_TYPES:
            return self._create_error(
                "UNKNOWN_OBJECT_TYPE",
                f"Unknown object type: {obj_type}",
                token
            )
        
        return {
            "status": "VALID",
            "ast_component": {
                "type": obj_type,
                "identifier": identifier
            }
        }
    
    def _validate_metadata(self, token: dict) -> dict:
        """Validate META token and create MetadataNode."""
        scope, reversible_str, sensitivity, hrc_str = token["values"]
        
        # Validate reversible (already validated by grammar pattern)
        reversible = reversible_str == "true"
        
        # Validate sensitivity
        if sensitivity not in self.SENSITIVITY_VALUES:
            return self._create_error(
                "INVALID_METADATA_VALUE",
                f"Invalid sensitivity value: {sensitivity}",
                token
            )
        
        # Validate hrc_required (already validated by grammar pattern)
        hrc_required = hrc_str == "true"
        
        # Validate scope (non-empty identifier)
        if not scope or not re.fullmatch(self.IDENTIFIER_PATTERN, scope):
            return self._create_error(
                "AMBIGUOUS_SCOPE",
                f"Invalid or ambiguous scope: {scope}",
                token
            )
        
        return {
            "status": "VALID",
            "ast_component": {
                "scope": scope,
                "reversible": reversible,
                "sensitivity": sensitivity,
                "hrc_required": hrc_required
            }
        }
    
    def _validate_hard_no(self, ast_components: dict) -> dict:
        """Apply Hard-No invariant validation - structural only, no heuristics."""
        verb = ast_components["verb"]
        metadata = ast_components["metadata"]
        
        # Hard-No rule 1: irreversible deletion
        # Check if verb action is "delete" (case-insensitive as per grammar pattern)
        # and metadata reversible is false
        if verb["action"].lower() == "delete" and not metadata["reversible"]:
            return self._create_error(
                "HARD_NO_VIOLATION",
                "Irreversible deletion is prohibited",
                None
            )
        
        # Hard-No rule 2: financial mutation without HRC
        # Spec says: "financial mutation with sensitivity HIGH and hrc_required == false"
        # We only check structural conditions, not content
        if (verb["class"] == "MUTATE" and 
            verb["action"].lower() == "financial" and  # Explicit match only
            metadata["sensitivity"] == "HIGH" and
            not metadata["hrc_required"]):
            return self._create_error(
                "HARD_NO_VIOLATION",
                "High-sensitivity financial mutation requires HRC",
                None
            )
        
        # Note: Credential access heuristic removed as per spec
        # Hard-No rules only enforced via explicit structural conditions
        
        return {"status": "VALID"}
    
    def _create_error(self, error_code: ErrorCode, message: str, 
                     token_or_loc: Optional[Union[dict, Location]]) -> ValidationResult:
        """Create standardized error response."""
        if isinstance(token_or_loc, dict) and token_or_loc:
            location = {
                "line": token_or_loc.get("line"),
                "column": token_or_loc.get("column")
            }
        elif isinstance(token_or_loc, dict):
            location = token_or_loc
        else:
            location = {"line": None, "column": None}
        
        return {
            "status": "INVALID",
            "ast": None,
            "error": {
                "error_code": error_code,
                "message": message,
                "location": location
            }
        }


# === PUBLIC INTERFACE ===

def validate_dsl(input_text: str) -> ValidationResult:
    """Public pure function interface."""
    validator = DSLValidator()
    return validator.validate_dsl(input_text)