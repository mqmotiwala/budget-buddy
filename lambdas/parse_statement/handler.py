import boto3
import pandas as pd
import os

from parsers import chase, amex

ISSUER_PARSERS = {
    "chase": chase.parse,
    "amex": amex.parse,
}

s3 = boto3.client('s3')

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        # extract issuer from key path
        # expected format: statements/<issuer>/file.csv
        issuer = key.split("/")[1]  
        parser = ISSUER_PARSERS.get(issuer.lower())

        if not parser:
            raise ValueError(f"Unsupported or unrecognized issuer in key: {key}")

        obj = s3.get_object(Bucket=bucket, Key=key)
        raw = pd.read_csv(obj['Body'])

        clean = parser(raw)
        clean["statement_issuer"] = issuer.lower()

        filename = key.split("/")[-1]
        output_key = f"to_review/{issuer.lower()}/{filename}"

        s3.put_object(
            Bucket=bucket,
            Key=output_key,
            Body=clean.to_csv(index=False).encode('utf-8')
        )
