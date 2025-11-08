from typing import List, Dict, Any

class LayoutAnalyzer:
    def analyze(self, parsed_data: Dict[str, Any]) -> List[Dict]:
        elements = []

        tables = parsed_data.get('tables', [])
        for table in tables:
            bbox = table.get('bbox', {})
            elements.append({
                'type': 'table',
                'data': table,
                'bbox': bbox,
                'top': bbox.get('Top', 0),
                'left': bbox.get('Left', 0)
            })

        forms = parsed_data.get('forms', [])
        if forms:
            form_group_bbox = self._get_bounding_box_for_forms(forms)
            elements.append({
                'type': 'form',
                'data': forms,
                'bbox': form_group_bbox,
                'top': form_group_bbox.get('Top', 0),
                'left': form_group_bbox.get('Left', 0)
            })

        checkboxes = parsed_data.get('checkboxes', [])
        if checkboxes:
            checkbox_group_bbox = self._get_bounding_box_for_checkboxes(checkboxes)
            elements.append({
                'type': 'checkbox',
                'data': checkboxes,
                'bbox': checkbox_group_bbox,
                'top': checkbox_group_bbox.get('Top', 0),
                'left': checkbox_group_bbox.get('Left', 0)
            })

        text = parsed_data.get('text', '')
        bounding_boxes = parsed_data.get('bounding_boxes', [])
        if text:
            elements.append({
                'type': 'text',
                'data': {'text': text, 'bounding_boxes': bounding_boxes},
                'bbox': {'Top': 0, 'Left': 0},
                'top': 0,
                'left': 0
            })

        sorted_elements = self._sort_by_reading_order(elements)

        return sorted_elements

    def _sort_by_reading_order(self, elements: List[Dict]) -> List[Dict]:
        return sorted(elements, key=lambda e: (e['top'], e['left']))

    def _get_bounding_box_for_forms(self, forms: List[Dict]) -> Dict:
        if not forms:
            return {'Top': 0, 'Left': 0, 'Width': 0, 'Height': 0}

        tops = [f.get('bbox', {}).get('Top', 0) for f in forms]
        return {'Top': min(tops) if tops else 0, 'Left': 0, 'Width': 0, 'Height': 0}

    def _get_bounding_box_for_checkboxes(self, checkboxes: List[Dict]) -> Dict:
        if not checkboxes:
            return {'Top': 0, 'Left': 0, 'Width': 0, 'Height': 0}

        tops = [c.get('bbox', {}).get('Top', 0) for c in checkboxes]
        return {'Top': min(tops) if tops else 0, 'Left': 0, 'Width': 0, 'Height': 0}
