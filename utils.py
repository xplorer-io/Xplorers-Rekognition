import boto3
import datetime
import os

def compare_faces(collection_id, jpg_data, max_faces=1, face_match_threshold=70):
    """ 
    Compares faces with AWS Rekognition Collections
    """
    rekog = boto3.client('rekognition')

    return rekog.search_faces_by_image(
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
    user_id = face_data['FaceMatches'][0]['Face']['ExternalImageId']
    if user_id == 'UG31DMHGB':
        return 'Prasiddha'
        # print('You are {}'.format(emp_name))
    elif user_id == 'UG47CJXQX':
        return 'Bijay'
        # print('You are {}'.format(emp_name))    
        
def generate_mp3(user_name):
    """
    Generates an MP3 file from Polly and saves it on Deeplens Device
    """
    polly = boto3.client('polly')
    dt = datetime.datetime.now()
    
    if dt.hour < 12:
        greetingString = 'morning'
    elif dt.hour < 18:
        greetingString = 'afternoon'
    elif dt.hour >= 18:
        greetingString = 'evening'

    message = '<speak>\n<prosody rate=\"medium\"><amazon:breath duration=\"long\" volume=\"soft\"/>Good ' + greetingString + ', Welcome to the Office ' + user_name +' <amazon:breath duration=\"short\" volume=\"x-soft\"/></prosody>\n</speak>'
    
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
    mp3_path = '/tmp/static-files/{}.mp3'.format(user_name)

    if not os.path.exists(mp3_path):
        # Unable to find existing greeting for this user, so
        # generate new mp3 with Polly
        mp3 = generate_mp3(user_name)
        with open(mp3_path, 'wb') as outfile:
            outfile.write(mp3['AudioStream'].read())
        
    os.system('/usr/bin/play {}'.format(mp3_path))

# def play_mp3_files():
#     if os.path.exists('/tmp/static-files/{}.mp3'.format(user)):
#         os.system('/usr/bin/play /tmp/static-files/{}.mp3'.format(user))
#     else:       
#         outputFile = open('/tmp/static-files/{}.mp3'.format(user), 'wb')
#         outputFile.write(responsePolly['AudioStream'].read())
#         outputFile.close()
#         os.system('/usr/bin/play /tmp/static-files/{}.mp3'.format(user))