KEY_NAME="hadar111-`date +'%F'`"
KEY_PEM="$KEY_NAME.pem"

STACK_NAME="haddar-stack-6"

echo "create key pair $KEY_PEM to connect to instances and save locally"
#aws ec2 create-key-pair --key-name $KEY_NAME  --query "KeyMaterial" --output text > $KEY_PEM
# secure the key pair
#chmod 600 $KEY_PEM

# figure out my ip
echo "getting my ip"
MY_IP=$(curl ipinfo.io/ip)
echo "My IP: $MY_IP"


# get subnets for the ELB and vpc id
echo "getting all subnets and vpc id's"
VPC_ID=$(aws ec2 describe-subnets --filters Name=default-for-az,Values=true | jq -r .Subnets[0] | jq -r .VpcId)
VPC_CIDR_BLOCK=$(aws ec2 describe-vpcs --filters Name=vpc-id,Values=$VPC_ID | jq -r .Vpcs[0].CidrBlock)
echo $VPC_ID
echo $VPC_CIDR_BLOCK

echo "createing stack hadar stack"
STACK_RES=$(aws cloudformation create-stack --stack-name $STACK_NAME --template-body file://cloud-formation.yml --capabilities CAPABILITY_NAMED_IAM \
	--parameters ParameterKey=InstanceType,ParameterValue=t2.micro \
	ParameterKey=KeyName,ParameterValue=$KEY_NAME \
	ParameterKey=SSHLocation,ParameterValue=$MY_IP/32 \
	ParameterKey=VPCId,ParameterValue=$VPC_ID \
	ParameterKey=VPCcidr,ParameterValue=$VPC_CIDR_BLOCK)

echo "waiting for stack hadar-stack to be created"
STACK_ID=$(echo $STACK_RES | jq -r '.StackId')
echo $STACK_ID
aws cloudformation wait stack-create-complete --stack-name $STACK_ID

REGION=us-east-1

# get the wanted stack
STACK=$(aws cloudformation --region $REGION describe-stacks --stack-name $STACK_NAME | jq -r .Stacks[0])
# stack outputs
echo "printing stack outputs"
OUTPUTS=$(echo $STACK | jq -r .Outputs)
echo $OUTPUTS

echo "getting instances IP"
PUBLIC_IP_1=$(aws cloudformation --region $REGION describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='Instance1IP'].OutputValue" --output text)
#PUBLIC_IP_2=$(aws cloudformation --region $REGION describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='Instance2IP'].OutputValue" --output text)
INSTANCE_ID_1=$(aws cloudformation --region $REGION describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='InstanceId1'].OutputValue" --output text)
SG_FOR_WORKERS=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID_1 --query 'Reservations[*].Instances[*].[SecurityGroups[].GroupId |[*]]' --output text)

echo $INSTANCE_ID_1
echo $SG_FOR_WORKERS
echo $PUBLIC_IP_1
#echo $PUBLIC_IP_2


echo "waiting 200 seconds for all the dependecies to install, user data scripts takes time."
sleep 10

# echo "running the code"
ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_1 'cd cloud_computing/hw2 && python3 main.py $PUBLIC_IP_2' -eaf
#ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_1 "cd cloud_computing/hw2 && python3 auto_scaler.py $KEY_NAME $SG_FOR_WORKERS $PUBLIC_IP_1" -eaf
#ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_2 'cd cloud_computing/hw2 && python3 main.py $PUBLIC_IP_1' -eaf
#ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_2 "cd cloud_computing/hw2 && python3 auto_scaler.py $KEY_NAME $SG_FOR_WORKERS $PUBLIC_IP_2" -eaf

echo "done"

