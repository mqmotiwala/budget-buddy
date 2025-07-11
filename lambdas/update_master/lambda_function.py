"""
Lambda function to update master expenses file when new cleaned files are generated by parse_statement lambda function.
This function is triggered by S3 events when new cleaned files are uploaded.
"""

import json
import boto3
import pandas as pd
import logging
from datetime import datetime

from io import BytesIO
from urllib.parse import unquote_plus
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

BUCKET = 'aws-budget-buddy'
REQUIRED_COLS = ["transaction_id", "category", "notes"]
DEDUPLICATION_COLS = ["transaction_id"]

def lambda_handler(event, context):
    logger.info("Lambda triggered with event:")
    logger.info(json.dumps(event))

    try:
        body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        key = unquote_plus(body.get("parsed_statement_key", "KEY_NOT_FOUND_IN_EVENT_BODY"))

        logger.info(f"Processing file from bucket: {BUCKET}, key: {key}")

        # extract details from key path
        # expected format: <user>/cleaned/file.csv
        parts = key.split("/")
        user = parts[0]

        MASTER_KEY = f'{user}/categorized_expenses.parquet'
        BACKUP_FOLDER = f'{user}/backups'

        obj = s3.get_object(Bucket=BUCKET, Key=key)
        new_data = pd.read_csv(
            obj['Body'],
            dtype={
                'description': 'str',
                'amount': 'float64',
                'statement_issuer': 'str',
                'category': 'category',
                'notes': 'str'
            },
            parse_dates=['transaction_date'],
        )

        if new_data.empty:
            logger.warning(f"New file {key} is empty. Skipping update.")

            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Master file updated successfully"})
            }

        else:
            logger.info(f"Read {len(new_data)} rows from new CSV")

        # Load master file (if it exists)
        try:
            master_obj = s3.get_object(Bucket=BUCKET, Key=MASTER_KEY)
            master_body = BytesIO(master_obj['Body'].read())
            master_df = pd.read_parquet(master_body)

            num_rows = len(master_df)
            num_uncategorized = master_df['category'].isna().sum()
            logger.info(f"Read {num_rows} rows from master file")

            # Backup current copy of master file
            backup_key = f"{BACKUP_FOLDER}/{num_uncategorized}-{num_rows}__{datetime.now().strftime("%Y-%m-%dT%H-%M-%S-%f")}.parquet"
            s3.copy_object(
                Bucket=BUCKET,
                CopySource={'Bucket': BUCKET, 'Key': MASTER_KEY},
                Key=backup_key
            )

            logger.info(f"backed up latest master file at {backup_key}")

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning("Master file not found. Starting fresh.")
                master_df = pd.DataFrame(columns=new_data.columns)
            else:
                # streamlit checks for this log to confirm execution failure
                logger.error("FAILURE")
                logger.exception(f"Unable to process file {key}: {e}")
                
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": str(e)})
                }

        # include required columns in master schema
        # handles cases where master is empty or missing 
        for col in REQUIRED_COLS:
            if col not in master_df.columns:
                master_df[col] = pd.NA

        # Merge and deduplicate
        # we ignore columns that are not in both dataframes, handling categorized expenses gracefully
        combined = pd.concat([master_df, new_data], ignore_index=True)
        before = len(combined)
        combined = combined.drop_duplicates(subset=DEDUPLICATION_COLS)
        after = len(combined)
        logger.info(f"Dropped {before - after} duplicate rows. Final row count: {after}")

        # Save to Parquet in memory
        out_buffer = BytesIO()
        combined.to_parquet(out_buffer, index=False, compression='snappy')

        # Upload updated master file
        s3.put_object(
            Bucket=BUCKET,
            Key=MASTER_KEY,
            Body=out_buffer.getvalue()
        )

        logger.info(f"updated master file at {MASTER_KEY}")

        # check_lambda_completed() looks for this log to confirm execution success
        logger.info("SUCCESS")

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Master file updated successfully"})
        }

    except Exception as e:
        # check_lambda_completed() looks for this log to confirm execution failure
        logger.error("FAILURE")
        logger.exception(f"Unable to process file {key}: {e}")

        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }

