import boto3
import pandas as pd
import os
import logging

from config import ISSUER_CONFIG
from parser import parse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

def lambda_handler(event, context):
    logger.info(f"Lambda triggered with event: ")
    logger.info(event)

    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        logger.info(f"Processing file from bucket: {bucket}, key: {key}")

        try:
            # extract issuer from key path
            # expected format: statements/<issuer>/file.csv
            issuer = key.split("/")[1]
            if not ISSUER_CONFIG.get(issuer):
                raise ValueError(f"issuer {issuer} in key: {key} is unsupported/unrecognized")

            obj = s3.get_object(Bucket=bucket, Key=key)
            raw = pd.read_csv(obj['Body'])

            logger.info(f"Read {len(raw)} rows from raw CSV")

            clean = parse(raw, ISSUER_CONFIG[issuer])
            clean["statement_issuer"] = issuer.lower()

            filename = key.split("/")[-1]
            output_key = f"to_review/{issuer.lower()}/{filename}"

            logger.info(f"Uploading cleaned file to: {output_key}")
            
            s3.put_object(
                Bucket=bucket,
                Key=output_key,
                Body=clean.to_csv(index=False).encode('utf-8')
            )
            
        except Exception as e:
            logger.exception(f"Failed to process file {key}: {e}")
            raise
