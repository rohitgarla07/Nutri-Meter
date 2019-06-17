import json
import boto3
import time
import os
import botocore.session
from boto3.dynamodb.conditions import Key, Attr

region = "us-east-1"
dynamodb = boto3.client('dynamodb')

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


def lambda_handler(event, context):
    # TODO implement
    print(event)
    print(event['userName'])
    create_dynamo_table(event['userName'])
    
    return event
