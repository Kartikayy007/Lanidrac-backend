from typing import List, Dict, Tuple, Optional

class CheckboxConverter:
    def convert(self, checkboxes: List[Dict], bounding_boxes: List[Dict]) -> str:
        if not checkboxes:
            return ""

        text_blocks = [bb for bb in bounding_boxes if bb.get('type') == 'LINE']

        checkbox_items = []
        for checkbox in checkboxes:
            is_selected = checkbox.get('status') == 'SELECTED'
            label = self._find_checkbox_label(checkbox, text_blocks)
            checkbox_items.append((label, is_selected))

        return self._format_checklist(checkbox_items)

    def _find_checkbox_label(self, checkbox: Dict, text_blocks: List[Dict]) -> str:
        checkbox_bbox = checkbox.get('bbox', {})
        checkbox_left = checkbox_bbox.get('Left', 0)
        checkbox_top = checkbox_bbox.get('Top', 0)

        horizontal_threshold = 0.1
        vertical_threshold = 0.02
        above_threshold = 0.05

        horizontal_candidates = []
        vertical_candidates = []

        for block in text_blocks:
            block_bbox = block.get('bbox', {})
            block_left = block_bbox.get('Left', 0)
            block_top = block_bbox.get('Top', 0)
            text = block.get('text', '').strip()

            if not text:
                continue

            if abs(block_top - checkbox_top) < vertical_threshold:
                if block_left > checkbox_left and block_left - checkbox_left < horizontal_threshold:
                    distance = abs(block_left - checkbox_left)
                    horizontal_candidates.append((distance, text))

            if block_top < checkbox_top and checkbox_top - block_top < above_threshold:
                if abs(block_left - checkbox_left) < horizontal_threshold:
                    distance = checkbox_top - block_top
                    vertical_candidates.append((distance, text))

        if horizontal_candidates:
            horizontal_candidates.sort(key=lambda x: x[0])
            return horizontal_candidates[0][1]

        if vertical_candidates:
            vertical_candidates.sort(key=lambda x: x[0])
            return vertical_candidates[0][1]

        return "Checkbox"

    def _format_checklist(self, checkbox_items: List[Tuple[str, bool]]) -> str:
        lines = []

        for label, is_selected in checkbox_items:
            marker = "[x]" if is_selected else "[ ]"
            lines.append(f"- {marker} {label}")

        return "\n".join(lines)
