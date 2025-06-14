"""
Parse and clean financial statement CSV files uploaded to S3.
This Lambda function is triggered by S3 events when new files are uploaded to the 'statements' folder.
"""

import json
import boto3
import logging
import traceback
import pandas as pd

from config import ISSUER_CONFIG
from parser import parse
from urllib.parse import unquote_plus

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

BUCKET = 'aws-budget-buddy'

def lambda_handler(event, context):
    logger.info(f"Lambda triggered with event: ")
    logger.info(json.dumps(event))

    key = unquote_plus(event.get('key'))
    logger.info(f"Processing file from bucket: {BUCKET}, key: {key}")

    try:
        # extract details from key path
        # expected format: <user>/statements/<issuer>/file.csv
        parts = key.split("/")
        user = parts[0]
        issuer = parts[2]

        if not ISSUER_CONFIG.get(issuer):
            return {
                "statusCode": 422,
                "body": json.dumps({
                    "error": f"issuer {issuer} in key: {key} is unsupported/unrecognized"
                })
            }

        obj = s3.get_object(Bucket=BUCKET, Key=key)
        raw = pd.read_csv(obj['Body'])

        logger.info(f"Read {len(raw)} rows from raw CSV")

        clean = parse(raw, ISSUER_CONFIG[issuer])
        clean["statement_issuer"] = issuer.lower()

        output_key = None
        if not clean.empty:
            # set output key based on issuer and date range
            min_date = clean["transaction_date"].dropna().min().date().strftime("%Y-%m-%d")
            max_date = clean["transaction_date"].dropna().max().date().strftime("%Y-%m-%d")
            output_key = f"{user}/cleaned/{issuer.lower()} activity from {min_date} to {max_date}.csv"
            logger.info(f"Uploading cleaned file to: {output_key}")
            
            s3.put_object(
                Bucket=BUCKET,
                Key=output_key,
                Body=clean.to_csv(index=False).encode('utf-8')
            )

        else:
            logger.warning(f"file {key} for issuer {issuer} is empty after parsing. No output generated.")
        
        # check_lambda_completed() looks for this log to confirm execution success
        logger.info("SUCCESS")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "parsed_statement_key": output_key
            })
        }

        
    except Exception as e:
        # check_lambda_completed() looks for this log to confirm execution failure
        logger.error("FAILURE")
        logger.exception(f"Unable to process file {key}: {e}")
        
        tb = traceback.format_exc()
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": str(e),
                "traceback": tb
            })
        }