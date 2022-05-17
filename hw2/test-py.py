import os
import boto3
import random
import time
import sys

from redis_resc import redis_conn, redis_queue

list_of_all_workers = []


def terminate_worker_instance(instance_id):
    ec2_client = boto3.client("ec2", region_name="us-east-1")
    res = ec2_client.terminate_instances(
        InstanceId=[instance_id]
    )
    print(res)


def get_args():
    key_name = sys.argv[1]
    worker_sg = sys.argv[2]
    master_ip = sys.argv[3]
    print(key_name, worker_sg, master_ip)


def main():
    get_args()


if __name__ == "__main__":
    main()
