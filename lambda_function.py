import boto3
import json
from datetime import datetime
import math

print('Loading function')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Parking')


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
    path = event['rawPath']
    if "/entry" in path:
        return entry(event, context)
    elif "/exit" in path:
        return exit_parking(event)


def entry(event, context):
    plate = event['queryStringParameters']['plate']
    parking_lot = event['queryStringParameters']['parkingLot']
    request_id = context.aws_request_id + plate
    table.put_item(
        Item={'user_id': request_id, 'plate': plate, 'parkingLot': parking_lot,
              'entranceTime': int(datetime.now().timestamp())})
    return respond(None, request_id)


def exit_parking(event):
    ticket_id = event['queryStringParameters']['ticketId']
    table_item = table.get_item(Key={'user_id': ticket_id})
    price = get_price(table_item['Item']['entranceTime'])
    total_time_min = get_total_time_parked_min(table_item['Item']['entranceTime'])
    plate = table_item['Item']['plate']
    lot = table_item['Item']['parkingLot']
    print(table_item['Item']['entranceTime'])
    return respond(None, {'price': price, 'licensePlate': plate, 'total_time_min': total_time_min, 'parking_lot': lot})


def get_price(entrance_time):
    diff = int(datetime.now().timestamp()) - int(entrance_time)
    num_of_15_min_rounded_up = math.ceil((diff / 60) / 15)
    price = 10 * num_of_15_min_rounded_up
    return price


def get_total_time_parked_min(entrance_time):
    diff = (datetime.now().timestamp() - int(entrance_time)) / 60
    return diff
