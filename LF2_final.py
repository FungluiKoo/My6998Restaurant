# Source: https://github.com/sowmya-nittala/AWS-Dining-Concierge-chatbot/blob/b23154d60afc5a5db0f9076ed45052d0aa6502ec/lambda%20Functions/lf2.py

import boto3
import json
import requests
import random
from requests_aws4auth import AWS4Auth


def receiveMsgFromSqsQueue():
    sqs = boto3.client('sqs')
    queue_url = "https://sqs.us-east-1.amazonaws.com/175581589055/QueueForDiningPlanner"
    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=['SentTimestamp'],
        MaxNumberOfMessages=5,
        MessageAttributeNames=['All'],
        VisibilityTimeout=10,
        WaitTimeSeconds=0
        )
    # print(response)
    return response

# The function return list of business id
def findRestaurantFromElasticSearch(cuisine):
    region = 'us-east-1'
    service = 'es'
    credentials = boto3.Session(aws_access_key_id="AKIASRYL2NY77XLKCPAO",
                          aws_secret_access_key="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", 
                          region_name="us-east-1").get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    host = 'search-myrestaurant-cjgluxxv6qtzc4xxwm5kuwp56i.us-east-1.es.amazonaws.com'
    index = 'restaurants'
    url = 'https://' + host + '/' + index + '/_search'
    # i am just getting 3 buisiness id from es but its not random rn
    query = {
        "size": 10,
        "query": {
            "multi_match": {
                # "fields": ["categories"],
                "query": cuisine
            }
        }
    }
    headers = { "Content-Type": "application/json" }
    response = requests.get(url,auth=awsauth, headers=headers, data=json.dumps(query))
    res = response.json()
    print("BEGIN OF ES RESPONSE:\n",res,"\nEND OF ES RESPONSE")
    noOfHits = res['hits']['total']['value']
    assert(noOfHits>0)
    hits = res['hits']['hits']
    #print(noOfHits)
    #print(hits[0]['_id'])
    buisinessIds = []
    for hit in hits:
        buisinessIds.append(str(hit['_source']['id']))
    #print(len(buisinessIds))
    return buisinessIds

# function returns detail of all resturantids as a list(working)
def getRestaurantFromDb(restaurantIds):
    res = []
    client = boto3.resource('dynamodb')
    table = client.Table('6998restaurant')
    for id in restaurantIds:
        # print("FINDING ID:",id)
        response = table.get_item(Key={'id': id})
        res.append(response)
    return res

def getMsgToSend(restaurantDetails,message):
    msg = "Dear Valued Customer,\n\nThank you for using our chatbot. "
    if message:
        noOfPeople = message['MessageAttributes']['NoOfPeople']['StringValue']
        date = message['MessageAttributes']['Date']['StringValue']
        time = message['MessageAttributes']['Time']['StringValue']
        cuisine = message['MessageAttributes']['Cuisine']['StringValue']
        msg += f"Below are our recommendations of {cuisine} restaurants for {noOfPeople} people, on {date} at {time}:\n\n"
    else:
        msg += "We have found the following restaurants for you:\n\n"
    
    for i in range(len(restaurantDetails)):
        msg += f"* {i+1}. {restaurantDetails[i]['Item']['name']}, located at {', '.join(restaurantDetails[i]['Item']['location']['display_address'])}\n"
    
    msg += "\nEnjoy,\n6998 Dining Concierge Chatbot"
    return msg
    
def sendSMS(msgToSend,email):
    client = boto3.client("ses")
    # print("HERE",client)
    # sample phone number shown email="+12223334444"
    response = client.send_email(
        Destination={
            'BccAddresses': [
            ],
            'CcAddresses': [
            ],
            'ToAddresses': [
                email,
            ],
        },
        Message={
            'Body': {
                'Html': {
                    'Charset': 'UTF-8',
                    'Data': msgToSend,
                },
                'Text': {
                    'Charset': 'UTF-8',
                    'Data': msgToSend,
                },
            },
            'Subject': {
                'Charset': 'UTF-8',
                'Data': 'Your 6998 Dining Concierge Chatbot',
            },
        },
        Source='f.gu@columbia.edu',
    )
    # print(response)
    
def deleteMsg(receipt_handle):
    sqs = boto3.client('sqs')
    queue_url = "https://sqs.us-east-1.amazonaws.com/175581589055/QueueForDiningPlanner"
    sqs.delete_message(QueueUrl=queue_url,
    ReceiptHandle=receipt_handle
    )

def lambda_handler(event, context):
    # getting response from sqs queue
    sqsQueueResponse = receiveMsgFromSqsQueue()
    print("BEGIN of sqsQueueResponse:\n",sqsQueueResponse,"\nEND of sqsQueueResponse")
    if "Messages" in sqsQueueResponse.keys():
        # for i in range(2):
        #     message = None
        for message in sqsQueueResponse['Messages']:
            cuisine = message['MessageAttributes']['Cuisine']['StringValue']
            restaurantIds = findRestaurantFromElasticSearch(cuisine)
            # Assume that it returns a list of restaurantsIds
            # call some random function to select 3 from the list
            # print("FOUND",len(restaurantIds),"RESTAURANTS")
            restaurantIds = random.sample(restaurantIds, 3)
            restaurantDetails = getRestaurantFromDb(restaurantIds)
            # print("RESTAURANT DETAILS:\n",restaurantDetails,"\nEND of RESTAURANT DETAILS")
            # now we have all required details to send the sms
            # now we will create the required message using the details
            msgToSend = getMsgToSend(restaurantDetails,message)
            # print(msgToSend)
            # dont uncomment below line until required. There is max limit on msg
            email = "fungluikoo@gmail.com"#message['MessageAttributes']['Email']['StringValue']
            sendSMS(msgToSend,email)
            #now delete message from queue
            receipt_handle = message['ReceiptHandle']
            deleteMsg(receipt_handle)
        return {
            'statusCode': 200,
            'body': json.dumps('Good')
        }
    else:
        return {
            'statusCode': 204,
            'body': json.dumps('No Messages')
        }