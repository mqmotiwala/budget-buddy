import io
import json
import time
import boto3
import config as c
import pandas as pd
import utils.helpers as h

from io import BytesIO
from botocore.exceptions import ClientError

USERS_TABLE = "users-budget-buddy"

# initialize client
ddb = boto3.resource(
    "dynamodb",
    aws_access_key_id = c.AWS_ACCESS_KEY_ID,
    aws_secret_access_key = c.AWS_SECRET_ACCESS_KEY,
    region_name = c.AWS_REGION
)

class User:
    """
    this User object is used to contain all user-related methods
    instantiated during auth using the auth response payload

    the User class variable contains the src table for storing user data 
    
    for Streamlit apps, this object is loaded to st.session_state
    and used as the entry point for:
        - invoking user-related methods, or
        - accessing user-specific variables
    """

    table = ddb.Table(USERS_TABLE)

    def __init__(self, payload):
        self.user_id = payload.get("sub")
        
        if self.is_new_user():
            self.init_user_data(payload)
            self.set_user_data()
        
        else:
            self.get_user_data()
            self.update_last_login()

        self.load_budgetbuddy_user_variables()

    def is_new_user(self):
        response = self.table.get_item(Key={"user_id": self.user_id})

        # Item key exists if user_id in table
        return "Item" not in response
    
    def init_user_data(self, payload):
        """Extracts standard fields from ID token payload into instance variables."""

        # payload data
        self.name = payload.get("name")
        self.email = payload.get("email")
        self.first_name = payload.get("given_name")
        self.last_name = payload.get("family_name")
        self.picture_url = payload.get("picture")
        self.created_at = payload.get("iat", int(time.time()))

        # additional attributes
        self.num_logins = 1
        self.last_login = self.created_at

        # initialize as free-tier user
        self.amount_paid = 0
        self.is_premium = False
        self.became_premium_at = None
        self.stripe_customer_id = None

    def set_user_data(self):
        """update user data in DynamoDB"""
        # __dict__ contains all instance variables
        item = {k: v for k, v in self.__dict__.items()}
        self.table.put_item(Item=item)

    def get_user_data(self):
        """get user data from DynamoDB"""
        response = self.table.get_item(Key={"user_id": self.user_id})
        item = response.get("Item", {})

        for k, v in item.items():
            setattr(self, k, v)

    def get_user_attribute(self, attr_name):
        """Fetch a single attribute from DynamoDB."""
        response = self.table.get_item(
            Key={"user_id": self.user_id},
            ProjectionExpression=attr_name
        )

        attr = response.get("Item", {}).get(attr_name)

        # attach to self
        # useful for repeat access of attr without using more DynamoDB read-capacity units
        setattr(self, attr_name, attr)

        return attr

    def update_last_login(self):
        """Updates the last login timestamp."""
        self.last_login = int(time.time())

        self.table.update_item(
            Key={"user_id": self.user_id},
            UpdateExpression="SET last_login = :ts ADD num_logins :inc",
            ExpressionAttributeValues={
                ":ts": self.last_login,
                ":inc": 1
            }
        )

    # ---- project specific logic ----

    def update_num_uploads(self):
        """Updates the number of statements uploaded."""

        self.table.update_item(
            Key={"user_id": self.user_id},
            UpdateExpression="ADD num_uploads :inc",
            ExpressionAttributeValues={
                ":inc": 1
            }
        )

    def load_budgetbuddy_user_variables(self):
        """
        this method contains only project specific user variables
        """

        self.ROOT_FOLDER = self.email

        self.STATEMENTS_FOLDER = f"{self.ROOT_FOLDER}/statements"
        self.MASTER_KEY = f"{self.ROOT_FOLDER}/categorized_expenses.parquet"
        self.CATEGORIES_KEY = f"{self.ROOT_FOLDER}/categories.json"

        try:
            response = c.s3.get_object(Bucket=c.S3_BUCKET, Key=self.CATEGORIES_KEY)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                # user has no defined categories
                # initialize a default response object that will pass downstream commands
                response = {"Body": io.BytesIO(b"{}")}

        self.CATEGORIES_BODY = json.loads(response['Body'].read().decode("utf-8"))
        self.CATEGORIES = h.extract_categories(self.CATEGORIES_BODY)
        self.EXPENSES_CATEGORIES = h.extract_categories(self.CATEGORIES_BODY.get(c.EXPENSES_PARENT_CATEGORY_KEY, {}))
        self.NON_EXPENSES_CATEGORIES = h.extract_categories(self.CATEGORIES_BODY.get(c.NON_EXPENSES_PARENT_CATEGORY_KEY, {}))

        # existing issuers
        response = c.s3.list_objects_v2(Bucket=c.S3_BUCKET, Prefix=f"{self.STATEMENTS_FOLDER}/", Delimiter="/")

        # CommonPrefixes structure looks like: 
        # [{"Prefix":"mqmotiwala@gmail.com/statements/amazon/"}], so
        # .split('/')[-1] is an empty string
        # .split('/')[-2] is the statement issuer
        self.EXISTING_ISSUERS = [prefix["Prefix"].split("/")[-2] for prefix in response.get("CommonPrefixes", [])]

    def load_master(self):
        master = None

        # load master data
        try:
            response = c.s3.get_object(Bucket=c.S3_BUCKET, Key=self.MASTER_KEY)
            raw = response["Body"].read()
            buffer = BytesIO(raw)

            master = pd.read_parquet(buffer)
            master = master.sort_values(by=c.DATE_COLUMN, ascending=False)

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                # master doesn't exist, skip loading
                pass

        self.master = master

    def update_master(self, master):
        """
        Update master in S3 with the provided DataFrame.
        
        Args:
            master (pd.DataFrame): The DataFrame to upload as the new master.
        """
        # Save to Parquet in memory
        out_buffer = BytesIO()
        master.to_parquet(out_buffer, index=False, compression='snappy')

        # Upload updated master file
        c.s3.put_object(
            Bucket=c.S3_BUCKET,
            Key=f"{self.MASTER_KEY}",
            Body=out_buffer.getvalue()
        )