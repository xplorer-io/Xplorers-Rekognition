import json
import boto3
import requests
import hashlib
import os
from .dynamo_utils import RekognitionKnown, update_dynamo
from .faces_emotions import compare_faces, detect_faces

bucket_name = os.environ['UNKNOWN_BUCKET_NAME']
slack_token = os.environ['SLACK_API_TOKEN']
slack_channel_id = os.environ['SLACK_CHANNEL_ID']
slack_training_channel_id = os.environ['SLACK_TRAINING_CHANNEL_ID']
rekognition_collection_id = os.environ['REKOGNITION_COLLECTION_ID']
image_bucket = os.environ['KNOWN_BUCKET_NAME']

def guess(event, context):
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
        evaluate_face_match = compare_faces(rekognition_collection_id, image)
        print(evaluate_face_match)
        
        gather_emotions = detect_faces(event_bucket_name, key)
        print(gather_emotions)

    except Exception as ex:
        # no faces detected, delete image
        print("No faces found, deleting")
        s3.Object(bucket_name, key).delete()
        return

    if len(evaluate_face_match['FaceMatches']) == 0:
        # no known faces detected, let the users decide in slack
        print("No matches found, sending to unknown")
        new_key = 'unknown/%s.jpg' % hashlib.md5(key.encode('utf-8')).hexdigest()
        s3.Object(bucket_name, new_key).copy_from(CopySource='%s/%s' % (event_bucket_name, key))
        s3.ObjectAcl(bucket_name, new_key).put(ACL='public-read')
        s3.Object(bucket_name, key).delete()
        return
    else:
        print ("Face found")
        user_id = evaluate_face_match['FaceMatches'][0]['Face']['ExternalImageId']
        match_percentage = round(evaluate_face_match['FaceMatches'][0]['Similarity'])
        image_id = evaluate_face_match['FaceMatches'][0]['Face']['ImageId']
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
        
        # Known Person Details for Dynamo Records 
        username = resp.json()['user']['real_name']
        userid = resp.json()['user']['id']
        age_range = gather_emotions[0]['AgeRange']
        age = '{Low}-{High}'.format(**age_range)
        gender = gather_emotions[0]['Gender']['Value']
        smile = gather_emotions[0]['Smile']['Value']
        beard = gather_emotions[0]['Beard']['Value']
        
        emotions_list = gather_emotions[0]['Emotions']
        # The order of output for emotions from Rekognition is not always 
        # the same, so get specific emotion details
        for item in emotions_list:
            if item['Type'] == 'HAPPY':
                happiness_confidence = round(item['Confidence'], 2) # round to 2 numbers after decimal
            elif item['Type'] == 'SAD':
                sadness_confidence = round(item['Confidence'], 2)
            elif item['Type'] == 'ANGRY':
                angry_confidence = round(item['Confidence'], 2)  
        
        print(f'Printing Happy {happiness_confidence}')
        print(f'Printing Sad {sadness_confidence}')
        print(f'Printing Angry {angry_confidence}')
        
        # Update Dynamo with details of known person
        update_dynamo(username, userid, f'{match_percentage}%', image_id, \
            url, age, gender, smile, beard, f'{happiness_confidence}%', f'{sadness_confidence}%', f'{angry_confidence}%')

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