KEY_NAME="hadar6-`date +'%F'`"
KEY_PEM="$KEY_NAME.pem"

STACK_NAME="hadar-stack4"

echo "create key pair $KEY_PEM to connect to instances and save locally"
aws ec2 create-key-pair --key-name $KEY_NAME  --query "KeyMaterial" --output text > $KEY_PEM
# secure the key pair
chmod 600 $KEY_PEM

# get my ip
echo "getting my ip"
MY_IP=$(curl ipinfo.io/ip)
echo "My IP: $MY_IP"


# get subnets and vpc id
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
PRIVATE_IP_1=$(aws cloudformation --region $REGION describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='Instance1PrivateIp'].OutputValue" --output text)
PUBLIC_IP_2=$(aws cloudformation --region $REGION describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='Instance2IP'].OutputValue" --output text)
PRIVATE_IP_2=$(aws cloudformation --region $REGION describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='Instance2PrivateIp'].OutputValue" --output text)
INSTANCE_ID_1=$(aws cloudformation --region $REGION describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='InstanceId1'].OutputValue" --output text)
SG_FOR_WORKERS=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID_1 --query 'Reservations[*].Instances[*].[SecurityGroups[].GroupId |[*]]' --output text)

echo "First instance ID - "
echo $INSTANCE_ID_1
echo "Security group ID used for the stack (app ec2's and workers)"
echo $SG_FOR_WORKERS
echo "First instance public IP - "
echo $PUBLIC_IP_1
echo "First instance private IP - "
echo $PRIVATE_IP_1
echo "Second instance IP - "
echo $PUBLIC_IP_2
echo "Second instance private IP - "
echo $PRIVATE_IP_2


echo "waiting 300 seconds for all the dependencies to install, user data scripts takes time."
sleep 500

echo "running the code on first ec2"
ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_1 "nohup python3 /home/ubuntu/cloud_computing/hw2/main.py $PRIVATE_IP_2 > /dev/null 2>&1 &"
echo "changing redis conf"
ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_1 'cd cloud_computing/hw2 && sudo mv redis.conf /etc/redis/redis.conf'
echo "restarting redis"
ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_1 'sudo service redis-server restart'
#ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_1 "python3 /home/ubuntu/cloud_computing/hw2/auto_scaler.py $KEY_NAME $SG_FOR_WORKERS $PRIVATE_IP_1" -eaf
echo "running the code on second ec2"
ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_2 "nohup python3 /home/ubuntu/cloud_computing/hw2/main.py $PRIVATE_IP_1 > /dev/null 2>&1 &"
echo "changing redis conf"
ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_2 'cd cloud_computing/hw2 && sudo mv redis.conf /etc/redis/redis.conf'
echo "restarting redis"
ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_2 'sudo service redis-server restart'
#ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_2 "cd cloud_computing/hw2 && python3 auto_scaler.py $KEY_NAME $SG_FOR_WORKERS $PUBLIC_IP_2" -eaf

echo "done"

