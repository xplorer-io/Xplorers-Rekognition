import json
import boto3
import requests
import hashlib
import os
from urllib.parse import parse_qs
from .sns_handler import presign_get_object_from_s3, send_sns_notification

bucket_name = os.environ['UNKNOWN_BUCKET_NAME']
slack_token = os.environ['SLACK_API_TOKEN']
slack_channel_id = os.environ['SLACK_CHANNEL_ID']
slack_training_channel_id = os.environ['SLACK_TRAINING_CHANNEL_ID']
rekognition_collection_id = os.environ['REKOGNITION_COLLECTION_ID']


def unknown(event, context):
    key = event['Records'][0]['s3']['object']['key']
    get_url = presign_get_object_from_s3(bucket_name, key)
    send_sns_notification(get_url)
    data = {
        "channel": slack_training_channel_id,
        "text": "I don't know who this is, can you tell me?",
        "attachments": [
            {
                "image_url": "https://s3.amazonaws.com/%s/%s" % (bucket_name, key),
                "fallback": "Nope?",
                "callback_id": key,
                "attachment_type": "default",
                "actions": [{
                        "name": "username",
                        "text": "Select a username...",
                        "type": "select",
                        "data_source": "users"
                    },
                    {
                        "name": "discard",
                        "text": "Ignore",
                        "style": "danger",
                        "type": "button",
                        "value": "ignore",
                        "confirm": {
                            "title": "Are you sure?",
                            "text": "Are you sure you want to ignore and delete this image?",
                            "ok_text": "Yes",
                            "dismiss_text": "No"
                        }
                    }
                ]
            }
        ]
    }
    print(data)
    # foo = requests.post("https://slack.com/api/chat.postMessage", headers={'Content-Type':'application/json;charset=UTF-8', 'Authorization': 'Bearer %s' % slack_token}, json=data)
    foo = requests.post("https://slack.com/api/chat.postMessage", headers={'Content-Type':'application/json;charset=UTF-8', 'Authorization': 'Bearer %s' % slack_token}, json=data)
    
# curl -X POST -H 'Content-type: application/json' --data '{"text":"Hello, World!"}' https://hooks.slack.com/services/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

    print(foo.json())
