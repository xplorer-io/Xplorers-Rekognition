import boto3

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
    subject = 'Alert! Unknown person detected at the Office.'
    message = f'An unknown person detected on arrival at the office, here\'s a picture of the person, {signed_url}'
    client = boto3.client('sns')
    response = client.publish(
        TopicArn='xplorers-rekognition-deploy-master-sns-topic',
        Message=message,
        Subject=subject
        #MessageStructure='string'
        # MessageAttributes={
        #     'string': {
        #         'DataType': 'string',
        #         'StringValue': 'string',
        #         'BinaryValue': b'bytes'
        #     }
        #}
    )
