import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

print("Testing AWS Credentials...")
print(f"Access Key ID: {AWS_ACCESS_KEY_ID[:10]}..." if AWS_ACCESS_KEY_ID else "Access Key ID: NOT SET")
print(f"Region: {AWS_REGION}")

try:
    textract_client = boto3.client(
        'textract',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

    response = textract_client.detect_document_text(
        Document={
            'Bytes': b'dummy'
        }
    )

    print("\n❌ Unexpected success with dummy data")

except ClientError as e:
    error_code = e.response['Error']['Code']
    error_message = e.response['Error']['Message']

    if error_code == 'InvalidParameterException':
        print("\n✅ AWS Credentials are VALID!")
        print("   (Got expected error for invalid document format)")
    elif error_code == 'UnrecognizedClientException':
        print("\n❌ AWS Credentials are INVALID!")
        print(f"   Error: {error_message}")
    else:
        print(f"\n❓ Got error code: {error_code}")
        print(f"   Message: {error_message}")

except Exception as e:
    print(f"\n❌ Unexpected error: {str(e)}")

print("\n--- Checking STS (AWS Identity) ---")
try:
    sts_client = boto3.client(
        'sts',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

    identity = sts_client.get_caller_identity()
    print("✅ Successfully authenticated!")
    print(f"   Account ID: {identity['Account']}")
    print(f"   User ARN: {identity['Arn']}")
    print(f"   User ID: {identity['UserId']}")

except ClientError as e:
    print(f"❌ STS Error: {e.response['Error']['Code']}")
    print(f"   Message: {e.response['Error']['Message']}")
