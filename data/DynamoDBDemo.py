import json
import boto3
from botocore.exceptions import ClientError
from american import american
from chinese import chinese
from indian import indian
from japanese import japanese
from mexican import mexican

restaurants = american + chinese + indian + japanese + mexican

for restaurant in restaurants:
    restaurant.pop("alias", None)
    restaurant.pop("image_url", None)
    restaurant.pop("is_closed", None)
    restaurant.pop("url", None)
    restaurant.pop("transactions", None)
    restaurant.pop("price", None)
    restaurant.pop("distance", None)
    restaurant["rating"] = str(restaurant["rating"])
    restaurant["coordinates"]["latitude"] = str(restaurant["coordinates"]["latitude"])
    restaurant["coordinates"]["longitude"] = str(restaurant["coordinates"]["longitude"])

def create_json():
    with open('data.json', 'w') as f:
        i = 0
        for restaurant in restaurants:
            f.write('{"index": {"_index": "restaurants", "_id": "'+restaurant['id']+'"}}\n')
            f.write(json.dumps(restaurant))
            f.write('\n')

# create_json()

def lambda_handler(event, context):
    # uni is the primary/paritition key
    # note they all have unique attributes
    
    # 1
    insert_data(restaurants)
    # 2
    lookup_data({'id': 'AA9wpuJRhkSHUePAiv3otA'})
    # 3
    # update_item({'uni': 'xx777'}, 'Canada')
    # 4
    # delete_item({'uni': 'xx777'})

    return


def insert_data(data_list, db=None, table='6998restaurant'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    # overwrite if the same index is provided
    for data in data_list:
        response = table.put_item(Item=data)
    print('@insert_data: response', response)
    return response


def lookup_data(key, db=None, table='6998restaurant'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    try:
        response = table.get_item(Key=key)
    except ClientError as e:
        print('Error', e.response['Error']['Message'])
    else:
        print(response['Item'])
        return response['Item']


def update_item(key, feature, db=None, table='6998restaurant'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    # change student location
    response = table.update_item(
        Key=key,
        UpdateExpression="set #feature=:f",
        ExpressionAttributeValues={
            ':f': feature
        },
        ExpressionAttributeNames={
            "#feature": "from"
        },
        ReturnValues="UPDATED_NEW"
    )
    print(response)
    return response


def delete_item(key, db=None, table='6998restaurant'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    try:
        response = table.delete_item(Key=key)
    except ClientError as e:
        print('Error', e.response['Error']['Message'])
    else:
        print(response)
        return response
