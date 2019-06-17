import json
import boto3

def lambda_handler(event, context):
    
    tableName = event['queryStringParameters']['user']
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

    table = dynamodb.Table(tableName)
    
    response = table.scan(
        Limit=15,
        )
    
    # final data to be sent to the webApp
    final_data = {}
    d = {}
    
    for i in response['Items']:
        d[i['meals']] = json.loads(i['nutrients'])
        image = json.loads(i['imageURL'])
        d[i['meals']]['imgURL'] = image['img']
    print(d)
    final_data['meals'] = d    
    
    final_json = json.dumps(final_data)

    httpresponse = {
            "statusCode": str(200),
            "headers": {
            "Access-Control-Allow-Origin" : "*", # Required for CORS support to work
            "Access-Control-Allow-Credentials" : "true" # Required for cookies, authorization headers with HTTPS
        },
        "body": final_json
    }
    
    return httpresponse