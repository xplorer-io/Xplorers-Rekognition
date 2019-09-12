
from datetime import datetime, timedelta, time
import pytz
from boto3 import session
from pynamodb.models import Model
from pynamodb.constants import STRING
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute, BooleanAttribute

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
    match_percentage = UnicodeAttribute(null=False)
    image_id = UnicodeAttribute(null=False)
    captured_at = UnicodeAttribute(default=time_now)
    image_url = UnicodeAttribute(null=False)
    age_range = UnicodeAttribute(null=False)
    gender = UnicodeAttribute(null=False)
    is_smiling = BooleanAttribute(null=False)
    has_beard = BooleanAttribute(null=False)
    is_happy = UnicodeAttribute(null=False)
    is_sad = UnicodeAttribute(null=False)
    is_angry = UnicodeAttribute(null=False)

def update_dynamo(username, userid, match_percentage, image_id, url, \
    age, gender, smile, beard, happy, sad, angry):
    """
    This function updates known-faces dynamo table with the data derived from Slack and AWS Rekognition
    """
    
    put_into_dynamo = RekognitionKnown(
        user_name = username,
        slack_user_id = userid,
        match_percentage = match_percentage,
        image_id = image_id,
        image_url = url,
        age_range = age,
        gender = gender,
        is_smiling = smile,
        has_beard = beard,
        is_happy = happy,
        is_sad = sad,
        is_angry = angry
    )
    put_into_dynamo.save()
