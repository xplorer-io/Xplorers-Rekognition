import boto3
rekognition = boto3.client('rekognition')

def compare_faces(rekognition_collection_id, image):
  """ 
  This functions compares the pictures from S3 and Rekognition to find a match
  """
  response = rekognition.search_faces_by_image(
		CollectionId=rekognition_collection_id,
		Image=image,
		MaxFaces=1,
		FaceMatchThreshold=70
  )
  return response

def detect_faces(bucket, key, attributes=['ALL']):
  """
  This function detects emotions from faces captured by AWS Deeplens
  """
  response = rekognition.detect_faces(
	    Image={
			"S3Object": {
				"Bucket": bucket,
				"Name": key,
			}
		},
	    Attributes=attributes,
	)
  return response['FaceDetails']
