import json
import os
import time
import unicodedata
import hashlib
import hmac

class SearchExecutor:
    SUPPORTED_CAPABILITIES = {"SEARCH_FILES", "SEARCH_EMAILS", "SEARCH_DATASETS"}
    
    def __init__(self, scope_allowlist, kernel_public_key, executor_private_key):
        self.scope_allowlist = scope_allowlist
        self.kernel_public_key = kernel_public_key
        self.executor_private_key = executor_private_key.encode()
    
    def _verify_lease_signature(self, lease):
        required = {"task_id", "issued_at", "expires_at", "signature"}
        if not all(k in lease for k in required):
            return False
        
        try:
            payload = f"{lease['task_id']}{lease['issued_at']}{lease['expires_at']}".encode()
            signature = lease["signature"]
            public_key = self.kernel_public_key
            return self._verify_signature(payload, signature, public_key)
        except Exception:
            return False
    
    def _verify_signature(self, payload, signature, public_key):
        raise NotImplementedError("verify_signature must be implemented by host")
    
    def _check_lease_expiry(self, lease):
        try:
            current_time = time.time()
            return current_time < lease["expires_at"]
        except Exception:
            return False
    
    def _sign_result(self, result_data):
        canonical = json.dumps(result_data, sort_keys=True, separators=(',', ':'))
        signature = hmac.new(self.executor_private_key, canonical.encode(), hashlib.sha256).hexdigest()
        return signature
    
    def _validate_query(self, query):
        if not isinstance(query, str):
            return False
        
        query = query.strip()
        if not query:
            return False
        
        try:
            query.encode('utf-8')
        except UnicodeError:
            return False
        
        try:
            normalized = unicodedata.normalize('NFC', query)
        except Exception:
            return False
        
        try:
            code_points = 0
            for _ in normalized:
                code_points += 1
            if code_points < 1 or code_points > 4096:
                return False
        except Exception:
            return False
        
        return True
    
    def _unicode_sort_key(self, s):
        if not isinstance(s, str):
            return []
        try:
            normalized = unicodedata.normalize('NFC', s)
            return [ord(cp) for cp in normalized]
        except Exception:
            return []
    
    def _generate_snippet(self, text, query):
        if not isinstance(text, str) or not isinstance(query, str):
            return ""
        
        try:
            text_norm = unicodedata.normalize('NFC', text)
            query_norm = unicodedata.normalize('NFC', query)
        except Exception:
            return ""
        
        idx = text_norm.find(query_norm)
        if idx == -1:
            return ""
        
        query_len = len(query_norm)
        
        snippet_chars = []
        char_count = 0
        
        start = max(0, idx - 100)
        end = min(len(text_norm), idx + query_len + 100)
        
        for i in range(start, end):
            snippet_chars.append(text_norm[i])
            char_count += 1
            if char_count >= 200:
                break
        
        return ''.join(snippet_chars)
    
    def _search_files(self, query, target_scope, max_results):
        if target_scope not in self.scope_allowlist:
            return {"error_code": "SCOPE_UNAVAILABLE"}
        
        scope_config = self.scope_allowlist.get(target_scope, {})
        root_path = scope_config.get("path")
        if not root_path or not isinstance(root_path, str):
            return {"error_code": "SCOPE_UNAVAILABLE"}
        
        try:
            if not os.path.exists(root_path):
                return {"error_code": "SCOPE_UNAVAILABLE"}
            if not os.path.isdir(root_path):
                return {"error_code": "SCOPE_UNAVAILABLE"}
        except OSError:
            return {"error_code": "SCOPE_UNAVAILABLE"}
        
        matches = []
        try:
            for dirpath, dirnames, filenames in os.walk(root_path, followlinks=False):
                dirnames[:] = [d for d in dirnames if not os.path.islink(os.path.join(dirpath, d))]
                
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.islink(filepath):
                        continue
                    
                    if query in filename:
                        try:
                            abs_path = os.path.abspath(filepath)
                            matches.append({
                                "id": abs_path,
                                "filename": filename,
                                "sort_key": self._unicode_sort_key(filename)
                            })
                        except OSError:
                            continue
        except OSError:
            return {"error_code": "EXECUTION_FAILED"}
        
        matches.sort(key=lambda x: x["sort_key"])
        count = len(matches)
        results = matches[:max_results]
        
        formatted = []
        for match in results:
            formatted.append({
                "id": match["id"],
                "match_field": "filename",
                "match_snippet": self._generate_snippet(match["filename"], query)
            })
        
        return {
            "results": formatted,
            "count": count,
            "truncated": count > max_results
        }
    
    def _search_emails(self, query, target_scope, max_results):
        if target_scope not in self.scope_allowlist:
            return {"error_code": "SCOPE_UNAVAILABLE"}
        
        scope_config = self.scope_allowlist.get(target_scope, {})
        email_source = scope_config.get("emails")
        if not isinstance(email_source, list):
            return {"error_code": "SCOPE_UNAVAILABLE"}
        
        matches = []
        try:
            import datetime
            for email in email_source:
                if not isinstance(email, dict):
                    continue
                
                email_id = email.get("id")
                timestamp_str = email.get("timestamp")
                
                if not email_id or not timestamp_str:
                    continue
                
                try:
                    dt = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if dt.tzinfo is None:
                        continue
                    dt_utc = dt.astimezone(datetime.timezone.utc)
                    timestamp = dt_utc.timestamp()
                except Exception:
                    continue
                
                matched = False
                match_field = ""
                match_text = ""
                
                for field in ["from", "to", "subject", "body"]:
                    field_value = email.get(field)
                    if isinstance(field_value, str) and query in field_value:
                        matched = True
                        match_field = field
                        match_text = field_value
                        break
                
                if matched:
                    matches.append({
                        "id": str(email_id),
                        "timestamp": timestamp,
                        "match_field": match_field,
                        "match_text": match_text
                    })
        except Exception:
            return {"error_code": "EXECUTION_FAILED"}
        
        matches.sort(key=lambda x: (x["timestamp"], x["id"]))
        count = len(matches)
        results = matches[:max_results]
        
        formatted = []
        for match in results:
            formatted.append({
                "id": match["id"],
                "match_field": match["match_field"],
                "match_snippet": self._generate_snippet(match["match_text"], query)
            })
        
        return {
            "results": formatted,
            "count": count,
            "truncated": count > max_results
        }
    
    def _search_datasets(self, query, target_scope, max_results):
        if target_scope not in self.scope_allowlist:
            return {"error_code": "SCOPE_UNAVAILABLE"}
        
        scope_config = self.scope_allowlist.get(target_scope, {})
        dataset = scope_config.get("dataset")
        if not isinstance(dataset, list):
            return {"error_code": "SCOPE_UNAVAILABLE"}
        
        matches = []
        try:
            for record in dataset:
                if not isinstance(record, dict):
                    continue
                
                record_id = record.get("id")
                if record_id is None:
                    continue
                
                matched = False
                match_field = ""
                match_text = ""
                
                for key, value in record.items():
                    if isinstance(value, str) and query in value:
                        matched = True
                        match_field = key
                        match_text = value
                        break
                
                if matched:
                    matches.append({
                        "id": str(record_id),
                        "primary_key": record_id,
                        "match_field": match_field,
                        "match_text": match_text
                    })
        except Exception:
            return {"error_code": "EXECUTION_FAILED"}
        
        try:
            matches.sort(key=lambda x: x["primary_key"])
        except Exception:
            return {"error_code": "EXECUTION_FAILED"}
        
        count = len(matches)
        results = matches[:max_results]
        
        formatted = []
        for match in results:
            formatted.append({
                "id": match["id"],
                "match_field": match["match_field"],
                "match_snippet": self._generate_snippet(match["match_text"], query)
            })
        
        return {
            "results": formatted,
            "count": count,
            "truncated": count > max_results
        }
    
    def execute_task(self, manifest, lease):
        if not self._verify_lease_signature(lease):
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "INVALID_LEASE",
                    "message": ""
                }
            }
        
        if not self._check_lease_expiry(lease):
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "LEASE_EXPIRED",
                    "message": ""
                }
            }
        
        if lease.get("task_id") != manifest.get("task_id"):
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "INVALID_LEASE",
                    "message": ""
                }
            }
        
        capability_id = manifest.get("capability_id")
        if capability_id not in self.SUPPORTED_CAPABILITIES:
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "UNSUPPORTED_CAPABILITY",
                    "message": ""
                }
            }
        
        inputs = manifest.get("inputs", {})
        query = inputs.get("query")
        target_scope = inputs.get("target_scope")
        max_results = inputs.get("max_results")
        
        if not self._validate_query(query):
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "INVALID_QUERY",
                    "message": ""
                }
            }
        
        if not target_scope or not isinstance(target_scope, str):
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "SCOPE_NOT_ALLOWED",
                    "message": ""
                }
            }
        
        if target_scope not in self.scope_allowlist:
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "SCOPE_NOT_ALLOWED",
                    "message": ""
                }
            }
        
        if not isinstance(max_results, int) or max_results < 1 or max_results > 1000:
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "INVALID_QUERY",
                    "message": ""
                }
            }
        
        query = query.strip()
        
        if capability_id == "SEARCH_FILES":
            result = self._search_files(query, target_scope, max_results)
        elif capability_id == "SEARCH_EMAILS":
            result = self._search_emails(query, target_scope, max_results)
        elif capability_id == "SEARCH_DATASETS":
            result = self._search_datasets(query, target_scope, max_results)
        else:
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": "EXECUTION_FAILED",
                    "message": ""
                }
            }
        
        if "error_code" in result:
            return {
                "status": "FAILURE",
                "error": {
                    "error_code": result["error_code"],
                    "message": ""
                }
            }
        
        output = {
            "task_id": manifest["task_id"],
            "capability_id": capability_id,
            "target_scope": target_scope,
            "results": result["results"],
            "count": result["count"],
            "truncated": result["truncated"]
        }
        
        result_to_sign = {
            "task_id": manifest["task_id"],
            "capability_id": capability_id,
            "status": "SUCCESS",
            "output": output
        }
        
        signature = self._sign_result(result_to_sign)
        
        return {
            "status": "SUCCESS",
            "output": output,
            "signature": signature
        }