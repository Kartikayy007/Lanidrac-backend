from typing import List, Dict, Optional

class TextConverter:
    def convert(self, text: str, bounding_boxes: List[Dict]) -> str:
        if not text:
            return ""

        line_blocks = [bb for bb in bounding_boxes if bb.get('type') == 'LINE']
        if not line_blocks:
            return text

        paragraphs = self._detect_paragraphs(line_blocks)

        output_lines = []
        for para in paragraphs:
            heading_level = self._detect_heading(para[0])

            if heading_level:
                para_text = " ".join([block.get('text', '').strip() for block in para])
                output_lines.append(f"{'#' * heading_level} {para_text}")
            else:
                formatted_para = self._format_with_hierarchy(para)
                output_lines.append(formatted_para)

        return "\n\n".join(output_lines)

    def _detect_paragraphs(self, blocks: List[Dict]) -> List[List[Dict]]:
        if not blocks:
            return []

        sorted_blocks = sorted(blocks, key=lambda b: (
            b.get('bbox', {}).get('Top', 0),
            b.get('bbox', {}).get('Left', 0)
        ))

        paragraphs = []
        current_paragraph = [sorted_blocks[0]]
        prev_bottom = sorted_blocks[0].get('bbox', {}).get('Top', 0) + \
                      sorted_blocks[0].get('bbox', {}).get('Height', 0.02)

        paragraph_gap_threshold = 0.03

        for block in sorted_blocks[1:]:
            current_top = block.get('bbox', {}).get('Top', 0)
            gap = current_top - prev_bottom

            if gap > paragraph_gap_threshold:
                paragraphs.append(current_paragraph)
                current_paragraph = [block]
            else:
                current_paragraph.append(block)

            prev_bottom = current_top + block.get('bbox', {}).get('Height', 0.02)

        if current_paragraph:
            paragraphs.append(current_paragraph)

        return paragraphs

    def _detect_heading(self, block: Dict) -> Optional[int]:
        text = block.get('text', '').strip()
        bbox = block.get('bbox', {})

        if not text:
            return None

        top_position = bbox.get('Top', 1.0)
        text_length = len(text)
        is_uppercase = text.isupper() and len(text) > 3
        is_short = text_length < 50

        if top_position < 0.15 and is_short:
            return 1

        if is_uppercase and is_short:
            return 2

        if is_short and text_length < 30 and text[0].isupper():
            if text.endswith(':'):
                return 3

        return None

    def _format_with_hierarchy(self, para: List[Dict]) -> str:
        if len(para) == 1:
            return para[0].get('text', '').strip()

        left_positions = [block.get('bbox', {}).get('Left', 0) for block in para]
        min_left = min(left_positions)

        indentation_threshold = 0.02

        lines = []
        for block in para:
            text = block.get('text', '').strip()
            left = block.get('bbox', {}).get('Left', 0)
            indent_diff = left - min_left

            if indent_diff > indentation_threshold:
                lines.append(f"  - {text}")
            else:
                lines.append(text)

        return "\n".join(lines)
