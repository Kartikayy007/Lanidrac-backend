import boto3
from typing import Dict, List
from botocore.exceptions import ClientError, BotoCoreError

from app.core.config import settings

class TextractClient:
    def __init__(self):
        self.client = boto3.client(
            'textract',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

        self.feature_types = ['TABLES', 'FORMS', 'SIGNATURES']

    def analyze_document(self, image_bytes: bytes) -> Dict:
        try:
            response = self.client.analyze_document(
                Document={'Bytes': image_bytes},
                FeatureTypes=self.feature_types
            )
            return response
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            raise Exception(f"Textract ClientError [{error_code}]: {error_message}")
        except BotoCoreError as e:
            raise Exception(f"Textract BotoCoreError: {str(e)}")
        except Exception as e:
            raise Exception(f"Textract Error: {str(e)}")

    def analyze_document_batch(self, image_bytes_list: List[bytes]) -> List[Dict]:
        responses = []
        for idx, image_bytes in enumerate(image_bytes_list):
            try:
                response = self.analyze_document(image_bytes)
                responses.append({
                    'page_number': idx + 1,
                    'response': response,
                    'status': 'success'
                })
            except Exception as e:
                responses.append({
                    'page_number': idx + 1,
                    'response': None,
                    'status': 'failed',
                    'error': str(e)
                })
        return responses
