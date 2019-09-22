
from datetime import datetime, timedelta, time
import pytz
from boto3 import session
from pynamodb.models import Model
from pynamodb.constants import STRING
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute, BooleanAttribute

def get_time():
    sydtz = pytz.timezone('Australia/Sydney')
    time_in_sydney = datetime.now(sydtz)
    time_now = str(time_in_sydney.strftime('%Y-%m-%d %H:%M:%S'))
    return time_now
class RekognitionKnown(Model):
    """
    Defines the Rekognition model for Known People's Database
    """
    class Meta:
        table_name = 'deeplens-known-faces'
        region = session.Session().region_name
        read_capacity_units = 5
        write_capacity_units = 5
    
    user_name = UnicodeAttribute(hash_key=True)
    slack_user_id = UnicodeAttribute(range_key=True)
    match_percentage = UnicodeAttribute(null=False)
    image_id = UnicodeAttribute(null=False)
    captured_at = UnicodeAttribute(default=get_time())
    image_url = UnicodeAttribute(null=False)
    age_range = UnicodeAttribute(null=False)
    gender = UnicodeAttribute(null=False)
    is_smiling = BooleanAttribute(null=False)
    has_beard = BooleanAttribute(null=False)
    is_happy = UnicodeAttribute(null=False)
    is_sad = UnicodeAttribute(null=False)
    is_angry = UnicodeAttribute(null=False)

class RekognitionUnknown(Model):
    """
    Defines the Rekognition model for Unknown People's Database
    """
    class Meta:
        table_name = 'deeplens-unknown-faces'
        region = session.Session().region_name
        read_capacity_units = 5
        write_capacity_units = 5
    
    captured_at = UnicodeAttribute(default=get_time())
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
    This function updates known-faces dynamo table with 
    the data derived from Slack and AWS Rekognition
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

def update_unknown_dynamo(url, age, gender, \
    smile, beard, happy, sad, angry):
    """
    This function updates unknown-faces dynamo table with 
    the data derived AWS Rekognition
    """
    put_into_unknown_dynamo = RekognitionUnknown(
        image_url = url,
        age_range = age,
        gender = gender,
        is_smiling = smile,
        has_beard = beard,
        is_happy = happy,
        is_sad = sad,
        is_angry = angry
    )
    put_into_unknown_dynamo.save()
