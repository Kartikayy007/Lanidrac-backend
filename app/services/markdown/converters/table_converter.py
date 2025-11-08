from typing import List, Dict

class TableConverter:
    def convert(self, table_data: Dict) -> str:
        if not table_data or 'rows' not in table_data:
            return ""

        rows = table_data['rows']
        if not rows or len(rows) == 0:
            return ""

        expanded_rows = self._handle_merged_cells(rows)
        has_header = self._detect_header(expanded_rows)

        return self._format_markdown_table(expanded_rows, has_header)

    def _handle_merged_cells(self, rows: List[List[Dict]]) -> List[List[str]]:
        result = []

        for row in rows:
            expanded_row = []
            for cell in row:
                text = cell.get('text', '').strip()
                row_span = cell.get('row_span', 1)
                col_span = cell.get('col_span', 1)

                if col_span > 1:
                    for _ in range(col_span):
                        expanded_row.append(text)
                else:
                    expanded_row.append(text)

            result.append(expanded_row)

        return result

    def _detect_header(self, rows: List[List[str]]) -> bool:
        if not rows:
            return False

        first_row = rows[0]
        if not first_row:
            return False

        non_empty_count = sum(1 for cell in first_row if cell.strip())
        return non_empty_count > 0

    def _format_markdown_table(self, rows: List[List[str]], has_header: bool) -> str:
        if not rows:
            return ""

        max_cols = max(len(row) for row in rows)

        for row in rows:
            while len(row) < max_cols:
                row.append("")

        col_widths = [0] * max_cols
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(cell))

        lines = []

        for idx, row in enumerate(rows):
            cells = [cell.ljust(col_widths[i]) for i, cell in enumerate(row)]
            lines.append("| " + " | ".join(cells) + " |")

            if idx == 0 and has_header:
                separator = ["-" * col_widths[i] for i in range(max_cols)]
                lines.append("| " + " | ".join(separator) + " |")

        return "\n".join(lines)
