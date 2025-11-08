from typing import Dict, List, Any

class TextractResponseParser:
    def __init__(self, response: Dict):
        self.response = response
        self.blocks = response.get('Blocks', [])
        self.block_map = {block['Id']: block for block in self.blocks}

    def _get_text(self, block_id: str) -> str:
        if block_id not in self.block_map:
            return ""

        block = self.block_map[block_id]

        if 'Text' in block:
            return block['Text']

        if 'Relationships' not in block:
            return ""

        text_parts = []
        for relationship in block['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    child_block = self.block_map.get(child_id)
                    if child_block and child_block.get('BlockType') == 'WORD':
                        text_parts.append(child_block.get('Text', ''))
        return ' '.join(text_parts)

    def extract_tables(self) -> List[Dict]:
        tables = []

        table_blocks = [block for block in self.blocks if block.get('BlockType') == 'TABLE']

        for table_block in table_blocks:
            table_data = {
                'id': table_block['Id'],
                'confidence': table_block.get('Confidence', 0),
                'rows': [],
                'bbox': table_block.get('Geometry', {}).get('BoundingBox', {})
            }

            if 'Relationships' not in table_block:
                tables.append(table_data)
                continue

            cells = []
            for relationship in table_block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for cell_id in relationship['Ids']:
                        cell_block = self.block_map.get(cell_id)
                        if cell_block and cell_block.get('BlockType') == 'CELL':
                            cells.append(cell_block)

            row_map = {}
            for cell in cells:
                row_index = cell.get('RowIndex', 1)
                col_index = cell.get('ColumnIndex', 1)

                if row_index not in row_map:
                    row_map[row_index] = {}

                cell_text = self._get_text(cell['Id'])
                row_map[row_index][col_index] = {
                    'text': cell_text,
                    'confidence': cell.get('Confidence', 0),
                    'row_span': cell.get('RowSpan', 1),
                    'col_span': cell.get('ColumnSpan', 1)
                }

            for row_idx in sorted(row_map.keys()):
                row_cells = [row_map[row_idx].get(col_idx, {'text': '', 'confidence': 0})
                             for col_idx in sorted(row_map[row_idx].keys())]
                table_data['rows'].append(row_cells)

            tables.append(table_data)

        return tables

    def extract_forms(self) -> List[Dict]:
        key_value_pairs = []

        key_blocks = [block for block in self.blocks
                      if block.get('BlockType') == 'KEY_VALUE_SET'
                      and 'KEY' in block.get('EntityTypes', [])]

        for key_block in key_blocks:
            key_text = self._get_text(key_block['Id'])

            value_text = ""
            if 'Relationships' in key_block:
                for relationship in key_block['Relationships']:
                    if relationship['Type'] == 'VALUE':
                        for value_id in relationship['Ids']:
                            value_text = self._get_text(value_id)

            key_value_pairs.append({
                'key': key_text,
                'value': value_text,
                'confidence': key_block.get('Confidence', 0),
                'bbox': key_block.get('Geometry', {}).get('BoundingBox', {})
            })

        return key_value_pairs

    def extract_checkboxes(self) -> List[Dict]:
        checkboxes = []

        selection_blocks = [block for block in self.blocks
                            if block.get('BlockType') == 'SELECTION_ELEMENT']

        for selection_block in selection_blocks:
            checkboxes.append({
                'id': selection_block['Id'],
                'status': selection_block.get('SelectionStatus', 'NOT_SELECTED'),
                'confidence': selection_block.get('Confidence', 0),
                'bbox': selection_block.get('Geometry', {}).get('BoundingBox', {})
            })

        return checkboxes

    def extract_bounding_boxes(self) -> List[Dict]:
        bboxes = []

        for block in self.blocks:
            if block.get('BlockType') in ['LINE', 'WORD', 'TABLE', 'CELL', 'KEY_VALUE_SET', 'SELECTION_ELEMENT']:
                bbox_data = {
                    'id': block['Id'],
                    'type': block['BlockType'],
                    'text': block.get('Text', ''),
                    'confidence': block.get('Confidence', 0),
                    'bbox': block.get('Geometry', {}).get('BoundingBox', {})
                }
                bboxes.append(bbox_data)

        return bboxes

    def parse(self) -> Dict[str, Any]:
        return {
            'tables': self.extract_tables(),
            'forms': self.extract_forms(),
            'checkboxes': self.extract_checkboxes(),
            'bounding_boxes': self.extract_bounding_boxes(),
            'document_metadata': self.response.get('DocumentMetadata', {})
        }
