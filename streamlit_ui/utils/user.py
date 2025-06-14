import time
import boto3
import config_general as c

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
    and used as the entry point for invoking user-related methods
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
