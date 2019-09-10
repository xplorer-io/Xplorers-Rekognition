
from datetime import datetime, timedelta, time
import pytz
from boto3 import session
from pynamodb.models import Model
from pynamodb.constants import STRING
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute, NumberAttribute

class RekognitionKnown(Model):
    """
    Defines the Rekognition model for Known People's DynamoDB
    """

    class Meta:
        table_name = 'deeplens-known-faces'
        region = session.Session().region_name
        read_capacity_units = 5
        write_capacity_units = 5
    
    sydtz = pytz.timezone('Australia/Sydney')
    time_in_sydney = datetime.now(sydtz)
    time_now = str(time_in_sydney.strftime('%Y-%m-%d %H:%M:%S'))
    
    user_name = UnicodeAttribute(hash_key=True)
    slack_user_id = UnicodeAttribute(range_key=True)
    match_percentage = NumberAttribute(null=False)
    image_id = UnicodeAttribute(null=False)
    captured_at = UnicodeAttribute(default=time_now)
    image_url = UnicodeAttribute(null=False)
    # sentiment analysis = ???
    
def update_dynamo(username, userid, match_percentage, image_id, url):
    """
    This function updates known-faces dynamo table with the data derived from Slack and Rekognition
    """
    
    put_into_dynamo = RekognitionKnown(
        user_name = username,
        slack_user_id = userid,
        match_percentage = round(match_percentage),
        image_id = image_id,
        image_url = url
    )
    put_into_dynamo.save()

class RekognitionUnKnown(Model):
    """
    Defines the Rekognition model for UnKnown People's DynamoDB
    """

    class Meta:
        table_name = 'deeplens-unknown-faces'
        region = session.Session().region_name
        read_capacity_units = 5
        write_capacity_units = 5
    
    sydtz = pytz.timezone('Australia/Sydney')
    time_in_sydney = datetime.now(sydtz)
    time_now = str(time_in_sydney.strftime('%Y-%m-%d %H:%M:%S'))
    
    #user_name = UnicodeAttribute(hash_key=True)
    #slack_user_id = UnicodeAttribute(range_key=True)
    #match_percentage = NumberAttribute(null=False)
    image_id = UnicodeAttribute(null=False)
    captured_at = UnicodeAttribute(default=time_now)
    image_url = UnicodeAttribute(null=False)
    # sentiment analysis = ???
    
def update_dynamo(match_percentage, image_id, url):
    """
    This function updates unknown-faces dynamo table
    """
    
    put_into_dynamo = RekognitionUnKnown(
        ##user_name = username,
        #slack_user_id = userid,
        match_percentage = round(match_percentage),
        image_id = image_id,
        image_url = url
    )
    put_into_dynamo.save()