from typing import Dict, Any, Optional, Tuple, List
import json
import re
import logging
from app.services.gemini.gemini_client import GeminiClient
from app.services.extract.schema_validator import SchemaValidator

logger = logging.getLogger(__name__)

class ExtractEngine:
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.validator = SchemaValidator()

    def extract_with_schema(
        self,
        schema: Dict[str, Any],
        image_bytes: bytes,
        mime_type: str = "image/png",
        textract_data: Optional[Dict] = None
    ) -> Tuple[Dict[str, Any], float]:
        extraction_prompt = self._build_extraction_prompt(schema)

        try:
            response = self.gemini_client.generate_with_image(
                prompt=extraction_prompt,
                image_bytes=image_bytes,
                mime_type=mime_type
            )

            extracted_json = self._parse_json_response(response)

            if not extracted_json:
                raise ValueError("Failed to extract valid JSON from Gemini response")

            is_valid, validation_errors, validation_results = self.validator.validate_data(
                extracted_json,
                schema
            )

            if validation_errors:
                logger.warning(f"Data validation warnings: {len(validation_errors)} issues found")
                for error in validation_errors[:5]:
                    logger.warning(f"  - {error}")

            confidence = self._calculate_confidence_from_validation(
                validation_results,
                textract_data
            )

            return extracted_json, confidence

        except Exception as e:
            logger.error(f"Extraction error: {str(e)}", exc_info=True)
            fallback_result = self._create_fallback_result(schema, textract_data)
            return fallback_result, 0.0

    def _build_extraction_prompt(self, schema: Dict[str, Any]) -> str:
        schema_json = json.dumps(schema, indent=2)

        prompt = f"""You are a document data extraction assistant. Extract information from the PROVIDED IMAGE by carefully reading the document and filling the JSON schema.

IMPORTANT INSTRUCTIONS:
1. Look at the IMAGE carefully - read all text, tables, checkboxes, and form fields
2. Return ONLY valid JSON that matches the schema structure exactly
3. Extract data by reading the visual document - preserve accuracy
4. Use null for missing values, never make up or hallucinate data
5. For arrays, extract all matching items found in the document image
6. For dates, use format YYYY-MM-DD
7. For numbers, extract numeric values only (no currency symbols)
8. For checkboxes: use true if checked, false if unchecked, null if not found
9. Do not include any explanation or markdown formatting in your response

JSON SCHEMA TO FILL:
{schema_json}

Look at the document image and extract the data. Return ONLY the JSON object matching the schema:"""

        return prompt

    def _parse_json_response(self, response: str) -> Optional[Dict]:
        response = response.strip()

        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            response = json_match.group(1)

        response = response.strip()
        if response.startswith('```'):
            response = re.sub(r'^```\w*\s*', '', response)
            response = re.sub(r'```$', '', response)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            lines = response.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('{'):
                    try:
                        json_text = '\n'.join(lines[i:])
                        return json.loads(json_text)
                    except:
                        continue

            return None

    def _calculate_confidence_from_validation(
        self,
        validation_results: Dict,
        textract_data: Optional[Dict] = None
    ) -> float:
        total = validation_results["total_fields"]
        valid = validation_results["valid_fields"]
        invalid = validation_results["invalid_fields"]
        missing = validation_results["missing_fields"]
        extra = validation_results["extra_fields"]

        if total == 0:
            return 0.0

        accuracy_score = valid / total if total > 0 else 0.0

        penalty = 0.0
        if invalid > 0:
            penalty += (invalid / total) * 0.3
        if missing > 0:
            penalty += (missing / total) * 0.2
        if extra > 0:
            penalty += min(extra / total, 0.2) * 0.1

        base_confidence = max(0.0, accuracy_score - penalty)

        if textract_data and base_confidence > 0:
            textract_verification = self._verify_with_textract(
                validation_results.get("type_errors", []),
                textract_data
            )
            confidence = (base_confidence * 0.8) + (textract_verification * 0.2)
        else:
            confidence = base_confidence

        return min(confidence, 1.0)

    def _verify_with_textract(
        self,
        type_errors: List[Dict],
        textract_data: Dict
    ) -> float:
        if not type_errors:
            return 1.0

        textract_text = self._extract_all_textract_text(textract_data)

        verified = 0
        for error in type_errors:
            value_str = str(error.get("value", ""))
            if value_str.lower() in textract_text.lower():
                verified += 1

        verification_rate = verified / len(type_errors) if type_errors else 1.0
        return verification_rate

    def _extract_all_textract_text(self, textract_data: Dict) -> str:
        all_text = []

        if 'forms' in textract_data:
            for form_item in textract_data.get('forms', []):
                key = form_item.get('key', '')
                val = form_item.get('value', '')
                if key:
                    all_text.append(key)
                if val:
                    all_text.append(val)

        if 'tables' in textract_data:
            for table in textract_data.get('tables', []):
                for row in table.get('rows', []):
                    for cell in row:
                        if cell:
                            all_text.append(str(cell))

        return ' '.join(all_text)

    def _count_schema_fields(self, obj: Any) -> int:
        if isinstance(obj, str):
            return 1
        elif isinstance(obj, dict):
            count = 0
            for value in obj.values():
                count += self._count_schema_fields(value)
            return count
        elif isinstance(obj, list) and len(obj) > 0:
            return 1
        return 0

    def _count_filled_fields(self, obj: Any) -> int:
        if obj is None:
            return 0
        elif isinstance(obj, (str, int, float, bool)):
            return 1 if obj else 0
        elif isinstance(obj, dict):
            count = 0
            for value in obj.values():
                count += self._count_filled_fields(value)
            return count
        elif isinstance(obj, list):
            return 1 if len(obj) > 0 else 0
        return 0

    def _calculate_textract_boost(
        self,
        extracted_data: Dict,
        textract_data: Dict
    ) -> float:
        boost = 0.0
        matches = 0
        total_checks = 0

        if 'forms' in textract_data:
            for form_item in textract_data.get('forms', []):
                total_checks += 1
                if self._value_in_extracted_data(form_item.get('value'), extracted_data):
                    matches += 1

        if 'tables' in textract_data:
            for table in textract_data.get('tables', []):
                for row in table.get('rows', []):
                    for cell in row:
                        if cell:
                            total_checks += 1
                            if self._value_in_extracted_data(cell, extracted_data):
                                matches += 0.5

        if total_checks > 0:
            boost = matches / total_checks

        return boost

    def _value_in_extracted_data(self, value: str, data: Any) -> bool:
        if not value:
            return False

        value_lower = str(value).lower()

        if isinstance(data, (str, int, float)):
            return value_lower in str(data).lower()
        elif isinstance(data, dict):
            for v in data.values():
                if self._value_in_extracted_data(value, v):
                    return True
        elif isinstance(data, list):
            for item in data:
                if self._value_in_extracted_data(value, item):
                    return True

        return False

    def _create_fallback_result(self, schema: Dict, textract_data: Optional[Dict] = None) -> Dict:
        result = {}

        if textract_data:
            logger.info("Attempting to extract from Textract data as fallback")
            textract_values = self._extract_textract_values(textract_data)

            for key, value in schema.items():
                if isinstance(value, str):
                    result[key] = self._find_matching_value(key, textract_values)
                elif isinstance(value, dict):
                    result[key] = self._create_fallback_result(value, textract_data)
                elif isinstance(value, list) and len(value) > 0:
                    result[key] = []
        else:
            for key, value in schema.items():
                if isinstance(value, str):
                    result[key] = None
                elif isinstance(value, dict):
                    result[key] = self._create_fallback_result(value, None)
                elif isinstance(value, list) and len(value) > 0:
                    result[key] = []

        return result

    def _extract_textract_values(self, textract_data: Dict) -> Dict[str, str]:
        values = {}

        if 'forms' in textract_data:
            for form_item in textract_data.get('forms', []):
                key = form_item.get('key', '').lower().strip()
                val = form_item.get('value', '').strip()
                if key and val:
                    values[key] = val

        if 'tables' in textract_data:
            for table in textract_data.get('tables', []):
                for row in table.get('rows', []):
                    if len(row) >= 2:
                        key = str(row[0]).lower().strip()
                        val = str(row[1]).strip()
                        if key and val:
                            values[key] = val

        return values

    def _find_matching_value(self, field_name: str, textract_values: Dict[str, str]) -> Optional[str]:
        field_lower = field_name.lower().replace('_', ' ')

        if field_lower in textract_values:
            return textract_values[field_lower]

        for key, value in textract_values.items():
            if field_lower in key or key in field_lower:
                return value

        return None