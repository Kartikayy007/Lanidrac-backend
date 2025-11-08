from typing import List, Dict

class FormConverter:
    def convert(self, forms: List[Dict]) -> str:
        if not forms:
            return ""

        return self._format_as_list(forms)

    def _format_as_list(self, forms: List[Dict]) -> str:
        lines = []

        for form in forms:
            key = form.get('key', '').strip()
            value = form.get('value', '').strip()

            if key and value:
                lines.append(f"**{key}:** {value}")
            elif key:
                lines.append(f"**{key}:** _[empty]_")

        return "\n".join(lines)

    def _group_by_proximity(self, forms: List[Dict]) -> List[List[Dict]]:
        if not forms:
            return []

        sorted_forms = sorted(forms, key=lambda f: (
            f.get('bbox', {}).get('Top', 0),
            f.get('bbox', {}).get('Left', 0)
        ))

        groups = []
        current_group = [sorted_forms[0]]
        current_top = sorted_forms[0].get('bbox', {}).get('Top', 0)

        threshold = 0.05

        for form in sorted_forms[1:]:
            top = form.get('bbox', {}).get('Top', 0)

            if abs(top - current_top) < threshold:
                current_group.append(form)
            else:
                groups.append(current_group)
                current_group = [form]
                current_top = top

        if current_group:
            groups.append(current_group)

        return groups
