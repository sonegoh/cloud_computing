import boto3
import json
from datetime import datetime

print('Loading function')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ParkingLot')


def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def lambda_handler(event, context):
    print("Lambda Request ID:", context.aws_request_id)
    print(datetime.now().isoformat())
    path = event['rawPath']
    if "/entry" in path:
        return entry(event, context)
    elif "/exit" in path:
        return exit_parking(event, context)
    # path_from_user = event['path']
    # print(f"path is {event['path']}")
    # return respond(None, "yey")


def entry(event, context):
    plate = event['queryStringParameters']['plate']
    request_id = 3;
    parking_lot = event['queryStringParameters']['parkingLot']
    table.put_item(
        Item={'id': request_id, 'palte': plate, 'parkingLot': parking_lot, 'entranceTime': datetime.now().isoformat()})
    return respond(None, "your in")


def exit_parking(event, context):
    # ticketId = event['queryStringParameters']['ticketId']
    ticketId = 5
    table_item = table.get_item(Key={'id': ticketId})
    # print(type(table_item))
    # print(table_item)
    print(table_item['Item']['entranceTime'])
    return respond(None, "out")
