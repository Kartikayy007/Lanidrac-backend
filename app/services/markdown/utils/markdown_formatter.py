import re
from typing import Dict

class MarkdownFormatter:
    @staticmethod
    def clean(markdown: str) -> str:
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)

        markdown = re.sub(r'(#{1,6} .+)\n{3,}', r'\1\n\n', markdown)

        lines = markdown.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip().startswith('|'):
                cleaned_lines.append(line)
            else:
                cleaned_lines.append(line.rstrip())

        return '\n'.join(cleaned_lines).strip()

    @staticmethod
    def validate(markdown: str) -> bool:
        if not markdown or not markdown.strip():
            return False

        return True

    @staticmethod
    def add_metadata(markdown: str, page_num: int, metadata: Dict) -> str:
        header_lines = [
            f"---",
            f"Page: {page_num}",
            f"Pages: {metadata.get('Pages', 1)}",
            f"---",
            "",
            markdown
        ]

        return "\n".join(header_lines)
