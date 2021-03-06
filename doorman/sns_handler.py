import boto3
import os

sns_arn = os.environ['SNS_TOPIC_ARN']

def presign_get_object_from_s3(bucket, key, expiration=3600, client=None):
    """
    Presign fetching object from s3.
    """
    if not client:
        client = boto3.client('s3')

    response = client.generate_presigned_url(
        ClientMethod='get_object',
        Params= {
            'Bucket': bucket,
            'Key': key
        },
        ExpiresIn=expiration
    )
    return response

def send_sns_notification(signed_url):
    """
    Send notification to the admins on findings from Deeplens
    """
    subject = 'Alert! Unknown person detected at the Office.'
    message = f'An unknown person detected at the office, here\'s a picture of the person, {signed_url}'
    client = boto3.client('sns')
    response = client.publish(
        TopicArn=sns_arn,
        Message=message,
        Subject=subject
    )
