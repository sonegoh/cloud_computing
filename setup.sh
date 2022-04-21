#!/bin/bash

REGION=$(aws ec2 describe-availability-zones | jq -r .AvailabilityZones[0].RegionName)
echo ${REGION}
AWS_ACCOUNT=$(aws sts get-caller-identity  | jq -r .Account)
echo ${AWS_ACCOUNT}
RUN_ID=$(date +'%M%S')
echo ${RUN_ID}
AWS_ROLE="lambda-role-$RUN_ID"
echo ${AWS_ROLE}
FUNC_NAME="my-func-$RUN_ID"
echo ${FUNC_NAME}
API_NAME="api-gateway-$RUN_ID"
echo ${API_NAME}
echo "Creating role $AWS_ROLE..."
aws iam create-role --role-name $AWS_ROLE --assume-role-policy-document file://trust-policy.json --no-cli-pager

echo "Allowing writes to CloudWatch logs..."
aws iam attach-role-policy --role-name $AWS_ROLE  \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole --no-cli-pager

echo "Allowing writes to Dynamo.."
aws iam attach-role-policy --role-name $AWS_ROLE  \
    --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess --no-cli-pager

echo "Packaging code..."
zip lambda.zip lambda_function.py

echo "Wait for role creation"
aws iam wait role-exists --role-name $AWS_ROLE --no-cli-pager
aws iam get-role --role-name $AWS_ROLE --no-cli-pager
ARN_ROLE=$(aws iam get-role --role-name $AWS_ROLE | jq -r .Role.Arn)
echo ${ARN_ROLE}

if ! aws dynamodb list-tables | jq -r .TableNames | grep -q Parking; then
  echo "Creating new DynamoDB table"
  aws dynamodb create-table \
      --table-name Parking \
      --attribute-definitions \
          AttributeName=user_id,AttributeType=S \
      --key-schema \
          AttributeName=user_id,KeyType=HASH \
      --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
      --no-cli-pager
fi


echo "Creating function $FUNC_NAME..."
aws lambda create-function --function-name $FUNC_NAME \
    --zip-file fileb://lambda.zip --handler lambda_function.lambda_handler \
    --runtime python3.9 --role $ARN_ROLE --no-cli-pager

FUNC_ARN=$(aws lambda get-function --function-name $FUNC_NAME | jq -r .Configuration.FunctionArn)

echo "Creating API Gateway..."
API_CREATED=$(aws apigatewayv2 create-api --name $API_NAME --protocol-type HTTP --target $FUNC_ARN)
API_ID=$(echo $API_CREATED | jq -r .ApiId)
API_ENDPOINT=$(echo $API_CREATED | jq -r .ApiEndpoint)

STMT_ID=$(uuidgen)

aws lambda add-permission --function-name $FUNC_NAME \
    --statement-id $STMT_ID --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:$AWS_ACCOUNT:$API_ID/*" --no-cli-pager