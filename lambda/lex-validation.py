import json
import boto3
import requests
import os

SQS = boto3.client("sqs")
client = boto3.client("sns")

def lambda_handler(event, context):

    query = event['currentIntent']['slots']['food']
    phone = event['currentIntent']['slots']['phone']
    
    edamam_url = "https://api.edamam.com/search?q="
    app_id = "xxxxxx"       # enter your api_id
    app_key = "xxxxxx"        # enter your app_key
    
    recipe = {}
    
    edamam_response = requests.get(edamam_url+query+"&app_id="+app_id+"&app_key="+app_key+"&from=1&to=2")

    edamam_response = edamam_response.json()
    recipe['name'] = edamam_response["hits"][0]["recipe"]["label"]
    recipe['url'] = edamam_response["hits"][0]["recipe"]["url"].replace(" ", "")
    recipe['healthLabels'] = edamam_response["hits"][0]["recipe"]["healthLabels"]
    recipe['ingredients'] = edamam_response["hits"][0]["recipe"]["ingredientLines"]
    recipe['instructions'] = edamam_response["hits"][0]["recipe"]["url"].replace(" ", "")
    
    outS = ""
    for i in range(len(recipe['ingredients'])):
        outS += str(i+1)+" : "+recipe['ingredients'][i]+";\n"
        
    outS += "For detailed instructions follow this link : \n"+recipe['instructions']
    
    # enter the edaman response to SQS service
    sqs_url = SQS.get_queue_url(QueueName="name_of_SQS")['QueueUrl']        # Enter the name of the SQS
    print(sqs_url)
    
    response_q_msg = SQS.send_message(
        QueueUrl=sqs_url,
        MessageBody=outS,
        DelaySeconds=12,
    )
    
    # try to send the data from the SQS to the SNS (message to user)
    try:
        response_send_msg = client.publish(
            PhoneNumber=phone,
            Message=outS,
            Subject='Nutri-Meter : Recipe Results'
        )
        
        # if successful then delete it from the SQS
        response_purge_q = SQS.purge_queue(
            QueueUrl=sqs_url
        )
    except:
        print("Error, notification failed!" )
    
    # send the response back to the lex
    result = {
        "dialogAction":{
            "type":"Close",
            "fulfillmentState":"Fulfilled",
            "message":{
                "contentType":"PlainText",
                "content":outS
            }
        }
    }
    return result