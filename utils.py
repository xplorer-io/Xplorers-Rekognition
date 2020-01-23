import boto3
import datetime
import os

def compare_faces(collection_id, jpg_data, max_faces=1, face_match_threshold=70):
    """
    Compares faces with AWS Rekognition Collections to find a match
    """
    rekognition = boto3.client('rekognition')

    return rekognition.search_faces_by_image(
        CollectionId=collection_id,
        Image={
            'Bytes': jpg_data.tobytes()
        },
        MaxFaces=max_faces,
        FaceMatchThreshold=face_match_threshold)


def verify_users(face_data):
    """
    Based on Rekognition's response, finds who the user is!
    """
    try:
        user_id = face_data['FaceMatches'][0]['Face']['ExternalImageId']
        if user_id == 'UG31DMHGB':
            print('Found a match! It\'s our homeboy Pras!')
            return 'Prasiddha'
        elif user_id == 'UG47CJXQX':
            print('Found a match! Legendary Bijay!')
            return 'Bijay'
    except:
        print('REKOGNITION says, "No Match Found!!"')

def generate_mp3(user_name):
    """
    Generates an MP3 file from Polly and saves it on Deeplens Device
    """
    polly = boto3.client('polly')

    message = '<speak>\n<prosody rate=\"medium\"><amazon:breath duration=\"long\" volume=\"soft\"/>Howdy ' + ', Welcome to the Office ' + user_name +' <amazon:breath duration=\"short\" volume=\"x-soft\"/></prosody>\n</speak>'

    return polly.synthesize_speech(
        OutputFormat = 'mp3',
        TextType = 'ssml',
        Text = message,
        VoiceId = 'Russell'
    )

def play_mp3_greeting(user_name):
    """
    Checks if an mp3 file exists for a given user,
    creates it if there is none, then plays it
    """
    mp3_path = '/tmp/{}.mp3'.format(user_name)

    if not os.path.exists(mp3_path):
        # Unable to find existing greeting for this user, so
        # generate new mp3 with Polly
        mp3 = generate_mp3(user_name)
        with open(mp3_path, 'w+') as outfile:
            outfile.write(mp3['AudioStream'].read())
            outfile.close()
            os.system('/usr/bin/play {}'.format(mp3_path))
    else:
        os.system('/usr/bin/play {}'.format(mp3_path))
