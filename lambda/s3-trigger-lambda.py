import requests
import json
import boto3
import time
import os
import botocore.session
from boto3.dynamodb.conditions import Key, Attr

region = "us-east-1"
dynamodb = boto3.client('dynamodb')

# to detect the labels from the images
def detect_label(PHOTO_BUCKET, FILE_NAME, event):
    label_list=[]
    
    print('reading image: {} from s3 bucket {}'.format(FILE_NAME, PHOTO_BUCKET))
    client = boto3.client('rekognition')
    response = client.detect_labels(
       Image={
           'S3Object': {
               'Bucket': PHOTO_BUCKET,
               'Name': FILE_NAME
           }
       },
       MaxLabels=10,
       MinConfidence=80,
    )
    
    print('Detected labels for ' + FILE_NAME)
    for label in response['Labels']:
       print (label['Name'] + ' : ' + str(label['Confidence']))
       label_list.append(label['Name'])
    
    edamam_url = "https://api.edamam.com/search?q="
    app_id = "xxxxxx"       # enter your api_id
    app_key = "xxxxxx"        # enter your app_key
    
    # "https://api.edamam.com/api/nutrition-details?app_id=${YOUR_APP_ID}&app_key=${YOUR_APP_KEY}"
    
    # to get the nutrient informations for the labels
    nutri = {}
    recipe = {}
    for label in label_list:
       if label != "Food":
            edamam_response = requests.get(edamam_url+label+"&app_id="+app_id+"&app_key="+app_key+"&from=0&to=2")
            edamam_response = edamam_response.json()
            
            recipe['name'] = edamam_response["hits"][0]["recipe"]["label"]
            recipe['url'] = edamam_response["hits"][0]["recipe"]["url"].replace(" ", "")
            recipe['healthLabels'] = edamam_response["hits"][0]["recipe"]["healthLabels"]
            recipe['ingredients'] = edamam_response["hits"][0]["recipe"]["ingredientLines"]
            recipe['instructions'] = edamam_response["hits"][0]["recipe"]["url"].replace(" ", "")
            
            yields = edamam_response["hits"][0]["recipe"]['yield']
            
            nutrients = edamam_response["hits"][0]["recipe"]['totalNutrients']
            try:
                nutri['Calories'] = nutrients['ENERC_KCAL']['quantity']/yields
            except:
                nutri['Calories'] = 0
            try:
                nutri['Fats'] = nutrients['FAT']['quantity']/yields
            except:
                nutri['Fats'] = 0
            try:
                nutri['SatFat'] = nutrients['FASAT']['quantity']/yields
            except:
                nutri['SatFat'] = 0
            try:
                nutri['Protein'] = nutrients['PROCNT']['quantity']/yields
            except:
                nutri['Protein'] = 0
            try:
                nutri['Cholestrol'] = nutrients['CHOLE']['quantity']/yields
            except:
                nutri['Cholestrol'] = 0
            try:
                nutri['Sodium'] = nutrients['NA']['quantity']/yields
            except:
                nutri['Sodium'] = 0
            try:
                nutri['Iron'] = nutrients['FE']['quantity']/yields
            except:
                nutri['Iron'] = 0
            try:
                nutri['Vitamin D'] = nutrients['VITD']['quantity']/yields
            except:
                nutri['Vitamin D'] = 0

    return json.dumps(recipe), json.dumps(nutri)

# to create the dynamo db table for the user
def create_dynamo_table(userName):
    session = botocore.session.get_session()
    dynamodb = session.create_client('dynamodb', region_name=region) # low-level client
    
    # Get the service resource.
    resource = boto3.resource('dynamodb')
    client   = boto3.client('dynamodb')
    
    table_to_create = userName
    
    print ("Checking if table exists")
    
    table_exists = False
    
    try:
        tabledescription = client.describe_table(TableName=table_to_create)
        print ("Table already exists")
        print ("Table descriptiuon:")
        print (tabledescription)
        table_exists = True

    except Exception as e:
        if "Requested resource not found: Table" in str(e):
            print ("Table does not exist")
            print ("Creating table")
            table = resource.create_table(
                    TableName = table_to_create,
                    
                    KeySchema = [{'AttributeName': 'meals'   ,'KeyType': 'HASH' }],
                                 
                    AttributeDefinitions =[{'AttributeName': 'meals','AttributeType': 'S' },],
                                           
                    ProvisionedThroughput={'ReadCapacityUnits': 5,'WriteCapacityUnits': 5}
                    )
        
            #wait for confirmation that the table exists
            table.meta.client.get_waiter('table_exists').wait(TableName=table_to_create)
            table_exists = True
        
        else:
            print ("Table cannot be created")
            raise
    return


def lambda_handler(event, context):
    
    for record in event['Records']:
        PHOTO_BUCKET = record['s3']['bucket']['name']
        FILE_NAME = record['s3']['object']['key']
        username = record['s3']['object']['key'].split("/")[0]
    
    imgURL = {'img':"https://s3.amazonaws.com/" + PHOTO_BUCKET + '/' + FILE_NAME}
    imgURL_dict = json.dumps(imgURL)

    #  detect label's from the image and get the recipe and nutrients dictionary
    recipe_dict, nutri_dict = detect_label(PHOTO_BUCKET, FILE_NAME, event)

    # create a table for the user if it does not exist
    create_dynamo_table(username)
    
    # push extracted parameters into the table
    last_index = 1
    try:
        for i in range(1, 10):
            last_index = i
            v = dynamodb.get_item(TableName=username, Key={'meals':{'S':'Meals_'+str(i)}})
            print(v)
            if v['Item']:
                pass
    except:
        pass
    
    item_param = {'meals':{'S':"Meals_"+str(last_index)},
                 'recipe': {'S' : recipe_dict}, 
                 'nutrients': {'S' : nutri_dict},
                 'imageURL':{'S' : imgURL_dict}
                }

    # put the item in the dynamo db
    dynamodb.put_item(TableName=username, Item=item_param)
    print("nothing found : ", i)