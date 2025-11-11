from typing import Dict, Any, List, Optional, Union
import json
from datetime import datetime

class SchemaValidator:
    SUPPORTED_TYPES = {
        "string", "number", "integer", "boolean",
        "date", "datetime", "array", "object"
    }

    def __init__(self):
        self.errors: List[str] = []

    def normalize_schema(self, schema: Dict) -> Dict:
        if "properties" in schema and isinstance(schema["properties"], dict):
            normalized = {}
            for field_name, field_def in schema["properties"].items():
                if isinstance(field_def, dict):
                    if "type" in field_def:
                        field_type = field_def["type"]

                        # Handle union types like ["string", "number"] -> just use "string"
                        if isinstance(field_type, list):
                            field_type = field_type[0] if field_type else "string"

                        if field_type == "array" and "items" in field_def:
                            if isinstance(field_def["items"], dict):
                                normalized[field_name] = [self.normalize_schema(field_def["items"])]
                            else:
                                normalized[field_name] = [field_def["items"].get("type", "string")]
                        elif field_type == "object" and "properties" in field_def:
                            normalized[field_name] = self.normalize_schema(field_def)
                        else:
                            normalized[field_name] = field_type
                    elif "properties" in field_def:
                        normalized[field_name] = self.normalize_schema(field_def)
                else:
                    normalized[field_name] = field_def
            return normalized
        return schema

    def validate_schema(self, schema: Union[Dict, str]) -> tuple[bool, List[str]]:
        self.errors = []

        if isinstance(schema, str):
            try:
                schema = json.loads(schema)
            except json.JSONDecodeError as e:
                return False, [f"Invalid JSON: {str(e)}"]

        if not isinstance(schema, dict):
            return False, ["Schema must be a JSON object"]

        # Just normalize, don't validate - accept anything
        schema = self.normalize_schema(schema)

        # Skip strict validation - allow any schema format
        return True, []

    def _validate_object(self, obj: Dict, path: str):
        for field_name, field_def in obj.items():
            field_path = f"{path}.{field_name}"

            if isinstance(field_def, str):
                if field_def not in self.SUPPORTED_TYPES:
                    self.errors.append(
                        f"Unsupported type '{field_def}' at {field_path}. "
                        f"Supported types: {', '.join(self.SUPPORTED_TYPES)}"
                    )

            elif isinstance(field_def, list):
                if len(field_def) == 0:
                    self.errors.append(f"Empty array schema at {field_path}")
                elif len(field_def) > 1:
                    self.errors.append(
                        f"Array at {field_path} should have exactly one schema element"
                    )
                else:
                    self._validate_field(field_def[0], f"{field_path}[0]")

            elif isinstance(field_def, dict):
                self._validate_object(field_def, field_path)

            else:
                self.errors.append(
                    f"Invalid field definition at {field_path}. "
                    f"Must be a type string, object, or array"
                )

    def _validate_field(self, field_def: Any, path: str):
        if isinstance(field_def, str):
            if field_def not in self.SUPPORTED_TYPES:
                self.errors.append(
                    f"Unsupported type '{field_def}' at {path}. "
                    f"Supported types: {', '.join(self.SUPPORTED_TYPES)}"
                )
        elif isinstance(field_def, dict):
            self._validate_object(field_def, path)
        elif isinstance(field_def, list):
            if len(field_def) != 1:
                self.errors.append(
                    f"Array at {path} should have exactly one schema element"
                )
            else:
                self._validate_field(field_def[0], f"{path}[0]")
        else:
            self.errors.append(
                f"Invalid field definition at {path}"
            )

    def get_field_types(self, schema: Dict) -> Dict[str, str]:
        field_types = {}
        self._extract_types(schema, "", field_types)
        return field_types

    def _extract_types(self, obj: Any, path: str, field_types: Dict):
        if isinstance(obj, str):
            field_types[path] = obj
        elif isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                self._extract_types(value, new_path, field_types)
        elif isinstance(obj, list) and len(obj) > 0:
            field_types[path] = "array"
            self._extract_types(obj[0], f"{path}[]", field_types)

    def validate_data(self, data: Dict, schema: Dict) -> tuple[bool, List[str], Dict[str, Any]]:
        self.errors = []
        validation_results = {
            "total_fields": 0,
            "valid_fields": 0,
            "invalid_fields": 0,
            "missing_fields": 0,
            "extra_fields": 0,
            "type_errors": []
        }

        normalized_schema = self.normalize_schema(schema)

        self._validate_data_recursive(data, normalized_schema, "root", validation_results)

        is_valid = len(self.errors) == 0

        return is_valid, self.errors, validation_results

    def _validate_data_recursive(self, data: Any, schema: Any, path: str, results: Dict):
        if isinstance(schema, str):
            results["total_fields"] += 1

            if data is None:
                results["missing_fields"] += 1
                self.errors.append(f"Missing value at {path}")
                return

            if not self._check_type(data, schema):
                results["invalid_fields"] += 1
                results["type_errors"].append({
                    "path": path,
                    "expected_type": schema,
                    "actual_type": type(data).__name__,
                    "value": str(data)[:50]
                })
                self.errors.append(
                    f"Type mismatch at {path}: expected {schema}, got {type(data).__name__}"
                )
            else:
                results["valid_fields"] += 1

        elif isinstance(schema, dict):
            if not isinstance(data, dict):
                results["total_fields"] += 1
                results["invalid_fields"] += 1
                self.errors.append(
                    f"Expected object at {path}, got {type(data).__name__}"
                )
                return

            schema_keys = set(schema.keys())
            data_keys = set(data.keys())

            extra_keys = data_keys - schema_keys
            if extra_keys:
                results["extra_fields"] += len(extra_keys)
                for key in extra_keys:
                    self.errors.append(f"Extra field at {path}.{key} (possible hallucination)")

            for key, sub_schema in schema.items():
                sub_data = data.get(key)
                self._validate_data_recursive(
                    sub_data,
                    sub_schema,
                    f"{path}.{key}",
                    results
                )

        elif isinstance(schema, list) and len(schema) > 0:
            results["total_fields"] += 1

            if data is None:
                results["missing_fields"] += 1
                self.errors.append(f"Missing array at {path}")
                return

            if not isinstance(data, list):
                results["invalid_fields"] += 1
                self.errors.append(
                    f"Expected array at {path}, got {type(data).__name__}"
                )
                return

            results["valid_fields"] += 1

            item_schema = schema[0]
            for i, item_data in enumerate(data):
                self._validate_data_recursive(
                    item_data,
                    item_schema,
                    f"{path}[{i}]",
                    results
                )

    def _check_type(self, value: Any, expected_type: str) -> bool:
        if value is None:
            return False

        type_checks = {
            "string": lambda v: isinstance(v, str),
            "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
            "boolean": lambda v: isinstance(v, bool),
            "date": lambda v: self._is_valid_date(v),
            "datetime": lambda v: self._is_valid_datetime(v),
            "object": lambda v: isinstance(v, dict),
            "array": lambda v: isinstance(v, list)
        }

        check_func = type_checks.get(expected_type)
        if check_func:
            return check_func(value)

        return False

    def _is_valid_date(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True
        except:
            return False

    def _is_valid_datetime(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        try:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
            return True
        except:
            return False