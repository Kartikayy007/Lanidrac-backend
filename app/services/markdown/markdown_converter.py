from typing import Dict, Any, List
from app.services.markdown.converters.table_converter import TableConverter
from app.services.markdown.converters.form_converter import FormConverter
from app.services.markdown.converters.checkbox_converter import CheckboxConverter
from app.services.markdown.converters.text_converter import TextConverter
from app.services.markdown.utils.layout_analyzer import LayoutAnalyzer
from app.services.markdown.utils.markdown_formatter import MarkdownFormatter

class MarkdownConverter:
    def __init__(self, parsed_data: Dict[str, Any], page_number: int = 1):
        self.parsed_data = parsed_data
        self.page_number = page_number
        self.table_converter = TableConverter()
        self.form_converter = FormConverter()
        self.checkbox_converter = CheckboxConverter()
        self.text_converter = TextConverter()
        self.layout_analyzer = LayoutAnalyzer()

    def convert(self) -> str:
        elements = self.layout_analyzer.analyze(self.parsed_data)

        markdown_parts = []
        full_text = self.parsed_data.get('text', '')

        for element in elements:
            element_type = element['type']
            element_data = element['data']

            if element_type == 'table':
                table_md = self.table_converter.convert(element_data)
                if table_md:
                    markdown_parts.append(table_md)

            elif element_type == 'form':
                if not self._forms_in_text(element_data, full_text):
                    form_md = self.form_converter.convert(element_data)
                    if form_md:
                        markdown_parts.append(form_md)

            elif element_type == 'checkbox':
                bounding_boxes = self.parsed_data.get('bounding_boxes', [])
                checkbox_md = self.checkbox_converter.convert(element_data, bounding_boxes)
                if checkbox_md:
                    markdown_parts.append(checkbox_md)

            elif element_type == 'text':
                text = element_data.get('text', '')
                bounding_boxes = element_data.get('bounding_boxes', [])
                text_md = self.text_converter.convert(text, bounding_boxes)
                if text_md:
                    markdown_parts.append(text_md)

        markdown = "\n\n".join(markdown_parts)

        markdown = MarkdownFormatter.clean(markdown)

        return markdown

    def _forms_in_text(self, forms: List[Dict], text: str) -> bool:
        if not forms or not text:
            return False

        text_lower = text.lower()
        match_count = 0

        for form in forms:
            key = form.get('key', '').strip().lower()
            value = form.get('value', '').strip().lower()

            if key and (key in text_lower or (value and value in text_lower)):
                match_count += 1

        match_threshold = 0.6

        return (match_count / len(forms)) >= match_threshold
