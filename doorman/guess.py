import json
import boto3
import requests
import hashlib
import os
from .dynamo_utils import RekognitionKnown, update_dynamo , update_unkown_dynamo, RekognitionUnKnown

bucket_name = os.environ['UNKNOWN_BUCKET_NAME']
slack_token = os.environ['SLACK_API_TOKEN']
slack_channel_id = os.environ['SLACK_CHANNEL_ID']
slack_training_channel_id = os.environ['SLACK_TRAINING_CHANNEL_ID']
rekognition_collection_id = os.environ['REKOGNITION_COLLECTION_ID']
image_bucket = os.environ['KNOWN_BUCKET_NAME']

def guess(event, context):
    client = boto3.client('rekognition')
    key = event['Records'][0]['s3']['object']['key']
    event_bucket_name = event['Records'][0]['s3']['bucket']['name']
    image = {
        'S3Object': {
            'Bucket': event_bucket_name,
            'Name': key
        }
    }
    # print(image)

    s3 = boto3.resource('s3') 

    try:
        resp = client.search_faces_by_image(
            CollectionId=rekognition_collection_id,
            Image=image,
            MaxFaces=1,
            FaceMatchThreshold=70)

    except Exception as ex:
        # no faces detected, delete image
        print("No faces found, deleting")
        s3.Object(bucket_name, key).delete()
        return

    if len(resp['FaceMatches']) == 0:
        # no known faces detected, let the users decide in slack
        print("No matches found, sending to unknown")
        new_key = 'unknown/%s.jpg' % hashlib.md5(key.encode('utf-8')).hexdigest()
        s3.Object(bucket_name, new_key).copy_from(CopySource='%s/%s' % (event_bucket_name, key))
        s3.ObjectAcl(bucket_name, new_key).put(ACL='public-read')
        s3.Object(bucket_name, key).delete()
        return
    else:
        print ("Face found")
        print (resp)
        user_id = resp['FaceMatches'][0]['Face']['ExternalImageId']
        match_percentage = resp['FaceMatches'][0]['Similarity']
        image_id = resp['FaceMatches'][0]['Face']['ImageId']
        # move image
        new_key = 'detected/%s/%s.jpg' % (user_id, hashlib.md5(key.encode('utf-8')).hexdigest())
        #Get the object key for generating url
        dynamo_key = '%s.jpg' % (hashlib.md5(key.encode('utf-8')).hexdigest())
        s3.Object(bucket_name, new_key).copy_from(CopySource='%s/%s' % (event_bucket_name, key))
        s3.ObjectAcl(bucket_name, new_key).put(ACL='public-read')
        #This is the object url of the captured picture
        url = f'https://{image_bucket}.s3.amazonaws.com/{key}'
        
        # fetch the username for this user_id
        data = {
            "token": slack_token,
            "user": user_id
        }

        resp = requests.post("https://slack.com/api/users.info", data=data)
        print(resp.content)
        # print(resp.json())
        username = resp.json()['user']['real_name']
        userid = resp.json()['user']['id']
        
        # Update Dynamo with details of known person
        update_dynamo(username, userid, match_percentage, image_id, url)

        if int(match_percentage) > 80:
            data = {
                "channel": slack_channel_id,
                "text": "Matched: {} (Similarity: {:.2f}%)".format(username, match_percentage),
                "link_names": True,
                "attachments": [
                    {
                        "image_url": "https://s3.amazonaws.com/%s/%s" % (bucket_name, new_key),
                        "fallback": "Nope?",
                        "callback_id": new_key,
                        "attachment_type": "default"
                    }
                ]
            }
            resp = requests.post("https://slack.com/api/chat.postMessage", headers={'Content-Type':'application/json;charset=UTF-8', 'Authorization': 'Bearer %s' % slack_token}, json=data)

        data = {
            "channel": slack_training_channel_id,
            "text": "Matched: {} (Similarity: {:.2f}%)".format(username, match_percentage),
            "link_names": True,
            "attachments": [
                {
                    "image_url": "https://s3.amazonaws.com/%s/%s" % (bucket_name, new_key),
                    "fallback": "Nope?",
                    "callback_id": new_key,
                    "attachment_type": "default",
                    "actions": [{
                            "name": "username",
                            "text": "Select a username...",
                            "type": "select",
                            "data_source": "users"
                        },
                        {
                            "name": "username",
                            "text": "Guess Was Right",
                            "style": "primary",
                            "type": "button",
                            "value": userid
                        }
                    ]
                }
            ]
        }


        resp = requests.post("https://slack.com/api/chat.postMessage", headers={'Content-Type':'application/json;charset=UTF-8', 'Authorization': 'Bearer %s' % slack_token}, json=data)

        return