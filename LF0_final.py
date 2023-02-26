import boto3

# Define the client to interact with Lex
client = boto3.client('lexv2-runtime')

def lambda_handler(event, context):
    # print(event)
    msg_from_user = event["messages"][0]["unstructured"]["text"]
    # msg_from_user = event['messages'][0]

    # change this to the message that user submits on 
    # your website using the 'event' variable
    # msg_from_user = "hello~"

    print(f"Message from frontend: {msg_from_user}")

    # Initiate conversation with Lex
    response = client.recognize_text(
            botId='AEAOTKJDIX', # MODIFY HERE
            botAliasId='TSTALIASID', # MODIFY HERE
            localeId='en_US',
            sessionId='testuser',
            text=msg_from_user)
    
    msg_from_lex = response.get('messages', [])
    if msg_from_lex:
        
        print(f"Message from Chatbot: {msg_from_lex[0]['content']}")
        print(response)

        resp = {
            'statusCode': 200,
            'body': "Hello from LF0!"
        }

        # modify resp to send back the next question Lex would ask from the user
        
        # format resp in a way that is understood by the frontend
        # HINT: refer to function insertMessage() in chat.js that you uploaded
        # to the S3 bucket

        if response['ResponseMetadata']['HTTPStatusCode'] == 200 :
            return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            "messages": [
                {
                "type": "unstructured",
                "unstructured": {
                    "id": "string",
                    "text": response['messages'][0]["content"],
                    "timestamp": "string"
                    }
                }
            ]
            }
        else:
            return resp


