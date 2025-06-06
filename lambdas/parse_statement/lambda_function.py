"""
Parse and clean financial statement CSV files uploaded to S3.
This Lambda function is triggered by S3 events when new files are uploaded to the 'statements' folder.
"""

import boto3
import pandas as pd
import os
import logging

from config import ISSUER_CONFIG
from parser import parse
from urllib.parse import unquote_plus

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

def lambda_handler(event, context):
    logger.info(f"Lambda triggered with event: ")
    logger.info(event)

    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])

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

            if not clean.empty:
                # set output key based on issuer and date range
                min_date = clean["transaction_date"].dropna().min().date().strftime("%Y-%m-%d")
                max_date = clean["transaction_date"].dropna().max().date().strftime("%Y-%m-%d")
                output_key = f"cleaned/{issuer.lower()} activity from {min_date} to {max_date}.csv"
                logger.info(f"Uploading cleaned file to: {output_key}")
                
                s3.put_object(
                    Bucket=bucket,
                    Key=output_key,
                    Body=clean.to_csv(index=False).encode('utf-8')
                )

            else:
                logger.warning(f"file {key} for issuer {issuer} is empty after parsing. No output generated.")
            
            # streamlit checks for this log to confirm execution success
            logger.info("SUCCESS")
            
        except Exception as e:
            # streamlit checks for this log to confirm execution failure
            logger.error("FAILURE")
            logger.exception(f"Unable to process file {key}: {e}")
            
            raise