# a handler that is triggered by an S3 event and converts a TIF file to a PNG file

import boto3
import os
from PIL import Image
import logging
from urllib.parse import unquote_plus
from botocore.exceptions import ClientError

s3 = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            img = Image.open(response['Body'])
            img.save('/tmp/image.png', 'PNG')
            s3.put_object(Body=open('/tmp/image.png', 'rb'), Bucket=os.environ['OUTPUT_BUCKET_NAME'], Key=key.replace('tif', 'png'))
        except ClientError as e:
            logger.error(e)
            return False
    return True