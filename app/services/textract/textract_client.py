import boto3
from typing import Dict, List
from botocore.exceptions import ClientError, BotoCoreError, ReadTimeoutError, ConnectTimeoutError
from botocore.config import Config

from app.core.config import settings

class TextractClient:
    def __init__(self):
        boto_config = Config(
            read_timeout=60,
            connect_timeout=10,
            retries={'max_attempts': 3, 'mode': 'standard'}
        )

        self.client = boto3.client(
            'textract',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            config=boto_config
        )

        self.feature_types = ['TABLES', 'FORMS', 'SIGNATURES']

    def analyze_document(self, image_bytes: bytes) -> Dict:
        try:
            response = self.client.analyze_document(
                Document={'Bytes': image_bytes},
                FeatureTypes=self.feature_types
            )
            return response
        except ReadTimeoutError:
            raise Exception("AWS processing timeout. Document may be too complex. Please try a smaller file.")
        except ConnectTimeoutError:
            raise Exception("AWS connection timeout. Please check your network and try again.")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']

            if error_code == 'ThrottlingException':
                raise Exception("AWS processing queue busy. Please wait a moment and try again.")
            elif error_code == 'ProvisionedThroughputExceededException':
                raise Exception("Service temporarily busy. Please try again in a few minutes.")
            elif error_code == 'InvalidParameterException':
                raise Exception("Invalid document format. Please upload a valid PDF or image file.")
            else:
                raise Exception(f"AWS processing failed: {error_message}")
        except BotoCoreError as e:
            raise Exception(f"AWS service error: {str(e)}")
        except Exception as e:
            raise Exception(f"Document processing failed: {str(e)}")

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
