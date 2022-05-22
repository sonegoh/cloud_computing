import boto3
import random
import time
import sys

from redis_resc import redis_queue

list_of_all_workers = []


# This will terminate ec2 instance by it's ID.
def terminate_worker_instance(instance_id):
    ec2_client = boto3.client("ec2", region_name="us-east-1")
    res = ec2_client.terminate_instances(
        InstanceId=[instance_id]
    )


# Create new ec2 instance that will automatically listen to the right queue.
def create_worker_instance():
    key_name = sys.argv[1]
    worker_sg = sys.argv[2]
    master_ip = sys.argv[3]
    ec2_client = boto3.client("ec2", region_name="us-east-1")
    worker_user_data = f"""#!/bin/bash
    sleep 10
    sudo apt-get update
    sudo apt-get install python3-pip -y
    sudo apt install python3-rq -y
    cd /home/ubuntu
    git clone https://github.com/sonegoh/cloud_computing.git
    cd cloud_computing/hw2
    rq worker --url redis://{master_ip}:6379
    """
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


# This will loop forever checking of there is need to scale up more nodes to cope with the pressure on the Queue.
# The same function will do the scale down if needed.
def workers_checker():
    while True:
        # Wait 200 sec before each scale up or down of instances.
        print("sleeping 200 secs")
        time.sleep(200)
        number_of_jobs_in_queue = len(redis_queue.jobs)
        print(number_of_jobs_in_queue)
        number_of_workers = len(list_of_all_workers)
        print(f"number of workers - {number_of_workers}")
        print(f"number of jobs - {number_of_jobs_in_queue}")
        if number_of_jobs_in_queue / number_of_workers > 100:
            # This is safety mechanism to no exceed the AWS free tier, i don't want to create tons of instances,
            # i want to have max value for that.
            if number_of_workers < 4:
                print("number of workers is less then 4")
                list_of_all_workers.append(create_worker_instance())
                print(f"list of workers - {list_of_all_workers}")
            else:
                print("number of workers is more then 4, we will not scale up more due to cost restrictions")
        elif number_of_jobs_in_queue / number_of_workers < 10:
            print(f"ratio of number_of_workers / number_of_workers is {number_of_workers / number_of_workers}")
            random_index = random.randint(0, number_of_workers - 1)
            print(f"rand index is {random_index}")
            print(f"removing the worker {list_of_all_workers[random_index]} from the list.")
            random_worker_to_kill = list_of_all_workers.pop(random_index)
            terminate_worker_instance(random_worker_to_kill)
        else:
            print("nothing to do, the scale is perfect")


def main():
    workers_checker()


if __name__ == "__main__":
    main()
