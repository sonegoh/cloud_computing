import os
import boto3
import random
import time

from redis_resc import redis_conn, redis_queue

list_of_all_workers = []


def terminate_worker_instance(instance_id):
    ec2_client = boto3.client("ec2", region_name="us-east-1")
    res = ec2_client.terminate_instances(
        InstanceId=[instance_id]
    )
    print(res)


def create_worker_instance():
    key_name = os.environ.get("KEY_NAME")
    worker_sg = os.environ.get("WORKER_SG")
    master_ip = os.environ.get("MY_IP")
    ec2_client = boto3.client("ec2", region_name="us-east-1")
    worker_user_data = f'''
        sleep 10
        sudo apt-get update
        sudo apt-get install python3-pip -y
        sudo apt install python3-rq -y
        cd /home/ubuntu
        git clone https://github.com/sonegoh/cloud_computing.git
        cd cloud_computing/hw2
        rq worker --url redis://{master_ip}:6379
    '''
    instances = ec2_client.run_instances(
        ImageId="ami-09d56f8956ab235b3",
        MinCount=1,
        MaxCount=1,
        InstanceType="t2.nano",
        KeyName=key_name,
        SecurityGroupIds=[worker_sg],
        UserData=worker_user_data
    )

    return instances["Instances"][0]["InstanceId"]


def workers_checker():
    while True:
        # Wait 100 sec before each scale up or down of instances.
        print("sleeping 10 secs")
        time.sleep(10)
        number_of_jobs_in_queue = len(redis_queue.jobs) + 200
        print(number_of_jobs_in_queue)
        number_of_workers = len(list_of_all_workers) + 1
        if number_of_jobs_in_queue / number_of_workers > 100:
            # This is safety mechanism to no exceed the AWS free tier.
            if number_of_workers < 4:
                print("number of workers is less then 4")
                #     list_of_all_workers.append(create_worker_instance())
                list_of_all_workers.append("i-11111")
                print(f"list of workers - {list_of_all_workers}")
            else:
                print("number of workers is more then 4, we will not scale up more due to $$$")
        elif number_of_workers / number_of_workers < 10:
            print(f"ratio of number_of_workers / number_of_workers is {number_of_workers / number_of_workers}")
            # random_worker_to_kill = random.sample(list_of_all_workers, 1)
            random_index = random.randint(0, number_of_workers - 1)
            print(f"removing the worker {list_of_all_workers[random_index]} from the list.")
            list_of_all_workers.pop(random_index)
            # terminate_worker_instance(random_worker_to_kill)


def main():
    workers_checker()


if __name__ == "__main__":
    main()
