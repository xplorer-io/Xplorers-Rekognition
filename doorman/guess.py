import json
import boto3
import requests
import hashlib
import os
import datetime
import subprocess
import pygame

bucket_name = os.environ['KNOWN_BUCKET_NAME']
slack_token = os.environ['SLACK_API_TOKEN']
slack_channel_id = os.environ['SLACK_CHANNEL_ID']
slack_training_channel_id = os.environ['SLACK_TRAINING_CHANNEL_ID']
rekognition_collection_id = os.environ['REKOGNITION_COLLECTION_ID']

polly = boto3.client('polly')

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
        similarity = resp['FaceMatches'][0]['Similarity']
        # move image
        new_key = 'detected/%s/%s.jpg' % (user_id, hashlib.md5(key.encode('utf-8')).hexdigest())
        s3.Object(bucket_name, new_key).copy_from(CopySource='%s/%s' % (event_bucket_name, key))
        s3.ObjectAcl(bucket_name, new_key).put(ACL='public-read')
        s3.Object(bucket_name, key).delete()

        # fetch the username for this user_id
        data = {
            "token": slack_token,
            "user": user_id
        }
        print(data)
        resp = requests.post("https://slack.com/api/users.info", data=data)
        print(resp.content)
        print(resp.json())
        username = resp.json()['user']['name']
        userid = resp.json()['user']['id']
        if user_id == 'UG31DMHGB':
            emp_name = 'Prasiddha'
            print(f'You are {emp_name}')
        elif user_id == 'UG47CJXQX':
            emp_name = 'Bijay'
            print(f'You are {emp_name}')
        dt = datetime.datetime.now()
        if dt.hour < 12:
            greetingString = 'morning'
        elif dt.hour < 18:
            greetingString = 'afternoon'
        elif dt.hour >= 18:
            greetingString = 'evening'
        message = '<speak>\n<prosody rate=\"medium\"><amazon:breath duration=\"long\" volume=\"soft\"/>Good ' + greetingString + ', Welcome to the Office ' + emp_name +' <amazon:breath duration=\"short\" volume=\"x-soft\"/></prosody>\n</speak>'
        responsePolly = polly.synthesize_speech(
			OutputFormat = 'mp3',
			TextType = 'ssml',
			Text = message,
			VoiceId = 'Russell'
		)
        print(responsePolly)
        ##############################################################
        # mp3Key = emp_name + ".mp3"
        # s3Client = boto3.client('s3')
        # if "AudioStream" in responsePolly:
        #     with closing(responsePolly["AudioStream"]) as stream:
        #         try:
        #             data = stream.read()
        #             song = AudioSegment.from_file(io.BytesIO(data), format="mp3")
        #             play(song)
        #         except IOError as error:
        #             print(error)
        #             sys.exit(-1)
        # sound1 = responsePolly['AudioStream'].read()

        # subprocess.run('play {}'.format(sound1),
        #                          shell=True,
        #                          check=True)
        # pygame.init()
        # pygame.mixer.init()
        # pygame.mixer.music.load(sound1)
        # pygame.mixer.music.play()
        # s3Response = s3Client.put_object(
        #     Bucket = 'audio-rekog-xplorers',
        #     Key = mp3Key,
        #     ACL = 'public-read',
        #     Body = responsePolly['AudioStream'].read(),
        #     ContentType = 'audio/mpeg'
        # )
        if int(similarity) > 80:
            data = {
                "channel": slack_channel_id,
                "text": "Matched: {} (Similarity: {:.2f}%)".format(username, similarity),
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
            "text": "Matched: {} (Similarity: {:.2f}%)".format(username, similarity),
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