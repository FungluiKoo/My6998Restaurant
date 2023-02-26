import json
import datetime
import time
import os
import dateutil.parser
import logging
import boto3
from botocore.exceptions import ClientError


def pushMsg(slots):
    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/175581589055/QueueForDiningPlanner'
    Attributes={
        'Cuisine': {
            'DataType': 'String',
            'StringValue': slots["Cuisine"]['value']['interpretedValue']
        },
        'NoOfPeople': {
            'DataType': 'String',
            'StringValue': slots["NumberOfPeople"]['value']['interpretedValue']
        },
        'Date': {
            'DataType': 'String',
            'StringValue': slots["DiningDate"]['value']['interpretedValue']
        },
        'Time': {
            'DataType': 'String',
            'StringValue': slots["DiningTime"]['value']['interpretedValue']
        },
        'Email' : {
            'DataType': 'String',
            'StringValue': slots["Email"]['value']['interpretedValue']
        }
    }
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageAttributes=Attributes,
        MessageBody=('Testing queue')
        )
    print("####response from sqs ####", response)
    print('###end of res from s')

def elicit_slot(intent_name, slots, slot_to_elicit, message):
    return {
            'sessionState': {
                'dialogAction': {
                    'type': 'ElicitSlot',
                    'slotToElicit': slot_to_elicit
                },
                'intent': {
                    'slots': slots,
                    'confirmationState': 'None',
                    'name': intent_name,
                    'state': 'InProgress'
                }
            },
            'messages': [message]
    }
    

def build_validation_result(isvalid, violated_slot, message_content):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

def isvalid_cuisine(cuisine):
    cuisines = ['american', 'indian', 'japanese', 'mexican', 'chinese']
    return cuisine.lower() in cuisines 

def isvalid_numberofpeople(numPeople):
    numPeople = int(numPeople)
    if numPeople > 99 or numPeople < 1:
        return False
    return True

def isvalid_date(diningDate):
    return datetime.datetime.strptime(diningDate, '%Y-%m-%d').date() >= datetime.date.today()

def isvalid_time(diningDate, diningtime):
    if datetime.datetime.strptime(diningDate, '%Y-%m-%d').date() == datetime.date.today():
        if datetime.datetime.strptime(diningtime, '%H:%M').time() <= datetime.datetime.now().time():
            return False
    return True

def isvalid_location(location):
    location = location.lower()
    locs = ['manhattan','new york','nyc', 'new york city', 'big apple']
    return location in locs
    

def validate_dining_suggestion(cuisine, numPeople, diningDate, diningTime,location):
    if location and not isvalid_location(location):
        return build_validation_result(False, 'Location', 'Sorry this location is currently not supported. Please try another (Manhattan/NYC/New York).')
    if cuisine and not isvalid_cuisine(cuisine):
        return build_validation_result(False, 'Cuisine', 'Cuisine not available. Please try another (American/Indian/Japanese/Mexican/Chinese).')
    if numPeople and not isvalid_numberofpeople(numPeople):
        return build_validation_result(False, 'NumberOfPeople', 'Maximum 99 people allowed. Please enter again.')
    if diningDate and not isvalid_date(diningDate):
        return build_validation_result(False, 'DiningDate', 'The date with the time entered is in the past. Please enter a valid dining date.')
    elif diningTime and diningDate and not isvalid_time(diningDate, diningTime):
        return build_validation_result(False, 'DiningTime', 'The time is in the past. Please enter a valid dining time.')
    
    return build_validation_result(True, None, None)


def lookup_user(email="fungluikoo@gmail.com", db=None, table='6998BotUsers'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    try:
        response = table.get_item(Key={"email":email})
    except ClientError as e:
        print('Error', e.response['Error']['Message'])
    else:
        print(response.get('Item', None))
        return response.get('Item', None)

def update_user(data, db=None, table='6998BotUsers'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    # overwrite if the same index is provided
    response = table.put_item(Item=data)
    print('@insert_data: response', response)
    return response


def dining_suggestions(event):
    slots = event['sessionState']['intent']['slots']
    email = slots["Email"]['value']['interpretedValue']   
    location = slots["Location"]['value']['interpretedValue']
    cuisine = slots["Cuisine"]['value']['interpretedValue']
    numPeople = slots["NumberOfPeople"]['value']['interpretedValue']
    diningdate = slots["DiningDate"]['value']['interpretedValue']
    diningtime = slots["DiningTime"]['value']['interpretedValue']
    validation_result = validate_dining_suggestion(cuisine, numPeople, diningdate, diningtime, location)
    if not validation_result['isValid']:
        slots[validation_result['violatedSlot']] = None
        return elicit_slot(event['sessionState']['intent']['name'], slots, validation_result['violatedSlot'], validation_result['message'])
    user_info = {'email': email,
                'Location': location,
                'Cuisine': cuisine,
                'NumberOfPeople': numPeople,
                'DiningDate': diningdate,
                'DiningTime': diningtime
                }
    update_user(user_info)
    pushMsg(slots)
    return {
        "sessionState": {
            "dialogAction": {
                "type": "Delegate",
            },
            "intent": {
                "name": "DiningSuggestionsIntent",
                "state": "Fulfilled"
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": "Thank you for using our service."
            }
        ]
    }

def reuse_intent(event):
    slots = event['sessionState']['intent']['slots']
    email = slots["Email"]['value']['interpretedValue'] 
    user_data = lookup_user(email)
    slots = {
        "Email": {
            "value": {
                "interpretedValue": user_data['email']
            }
        },
        "Cuisine": {
            "value": {
                "interpretedValue": user_data['Cuisine']
            }
        },
        "NumberOfPeople": {
            "value": {
                "interpretedValue": user_data['NumberOfPeople']
            }
        },
        "DiningDate": {
            "value": {
                "interpretedValue": user_data['DiningDate']
            }
        },
        "DiningTime": {
            "value": {
                "interpretedValue": user_data['DiningTime']
            }
        }
    }
    pushMsg(slots)
    return {
        "sessionState": {
            "dialogAction": {
                "type": "Delegate",
            },
            "intent": {
                "name": "Reuse",
                "state": "Fulfilled"
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": "Thank you for using our service."
            }
        ]
    }
    
def greetings(event):
    return {
        "sessionState": {
            "dialogAction": {
                "type": "Close",
            },
            "intent": {
                "name": "GreetingIntent",
                "state": "Fulfilled"
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": "Hi there, how can I help?"
            }
        ]
    }

def thankyou(event):
    return {
        "sessionState": {
            "dialogAction": {
                "type": "Close",
            },
            "intent": {
                "name": "ThankYouIntent",
                "state": "Fulfilled"
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": "You are welcome!"
            }
        ]
    }

def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    os.environ['TZ'] = 'America/New_York'
    time.tzset()

    intent_name = event['sessionState']['intent']['name']

    # route bot's intent
    if intent_name == 'GreetingIntent':
        return greetings(event)
    elif intent_name == 'ThankYouIntent':
        return thankyou(event)
    elif intent_name == 'Reuse':
        return reuse_intent(event)
    elif intent_name == 'DiningSuggestionsIntent':
        return dining_suggestions(event)

    raise Exception('Intent with name ' + intent_name + ' not supported')