KEY_NAME="hadar-`date +'%F'`"
KEY_PEM="$KEY_NAME.pem"

STACK_NAME="haddar-stack-1"

echo "create key pair $KEY_PEM to connect to instances and save locally"
aws ec2 create-key-pair --key-name $KEY_NAME  --query "KeyMaterial" --output text > $KEY_PEM
# secure the key pair
chmod 600 $KEY_PEM

# figure out my ip
echo "getting my ip"
MY_IP=$(curl ipinfo.io/ip)
echo "My IP: $MY_IP"


# get subnets for the ELB and vpc id
echo "getting all subnets and vpc id's"
#SUB_ID_1=$(aws ec2 describe-subnets --filters Name=default-for-az,Values=true | jq -r .Subnets[0] | jq -r .SubnetId)
#SUB_ID_2=$(aws ec2 describe-subnets --filters Name=default-for-az,Values=true | jq -r .Subnets[1] | jq -r .SubnetId)
#SUB_ID_3=$(aws ec2 describe-subnets --filters Name=default-for-az,Values=true | jq -r .Subnets[2] | jq -r .SubnetId)
#SUB_ID_4=$(aws ec2 describe-subnets --filters Name=default-for-az,Values=true | jq -r .Subnets[3] | jq -r .SubnetId)
VPC_ID=$(aws ec2 describe-subnets --filters Name=default-for-az,Values=true | jq -r .Subnets[0] | jq -r .VpcId)
VPC_CIDR_BLOCK=$(aws ec2 describe-vpcs --filters Name=vpc-id,Values=$VPC_ID | jq -r .Vpcs[0].CidrBlock)
#echo $SUB_ID_1
#echo $SUB_ID_2
#echo $SUB_ID_3
#echo $SUB_ID_4
echo $VPC_ID
echo $VPC_CIDR_BLOCK

echo "createing stack hadar stack"
STACK_RES=$(aws cloudformation create-stack --stack-name $STACK_NAME --template-body file://cloud-formation.yml --capabilities CAPABILITY_IAM \
	--parameters ParameterKey=InstanceType,ParameterValue=t2.nano \
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
PUBLIC_IP_2=$(aws cloudformation --region $REGION describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='Instance2IP'].OutputValue" --output text)
PUBLIC_IP_3=$(aws cloudformation --region $REGION describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='Instance3IP'].OutputValue" --output text)
PUBLIC_IP_4=$(aws cloudformation --region $REGION describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='Instance4IP'].OutputValue" --output text)

#DNS_ADD=$(aws elbv2 describe-load-balancers --names YaronandEdenELB | jq -r .LoadBalancers[0].DNSName)
#echo $DNS_ADD

# ssh-add ./$KEY_PEM

# echo "cloning repo"
# ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_1 'git clone https://github.com/edenbartov/cloud-computing.git'
# ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_2 'git clone https://github.com/edenbartov/cloud-computing.git'
# ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_3 'git clone https://github.com/edenbartov/cloud-computing.git'
# ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_4 'git clone https://github.com/edenbartov/cloud-computing.git'

# echo "waiting 10 seconds for all the dependecies to install"
# sleep 10

# echo "running the code"
# ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_1 'cd cloud-computing && python3 app.py' -eaf
# ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_2 'cd cloud-computing && python3 app.py' -eaf
# ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_3 'cd cloud-computing && python3 app.py' -eaf
# ssh -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@$PUBLIC_IP_4 'cd cloud-computing && python3 app.py' -eaf

echo "done"
