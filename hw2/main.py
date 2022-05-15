"""The Flask App."""

# pylint: disable=broad-except
import os

import boto3
from flask import Flask, abort, jsonify, request
from rq.job import Job
import random

from functions import hash_work
from redis_resc import redis_conn, redis_queue
import redis
from rq import Queue

# from rq.registry import FinishedJobRegistry


app = Flask(__name__)


@app.errorhandler(404)
def resource_not_found(exception):
    """Returns exceptions as part of a json."""
    return jsonify(error=str(exception)), 404


@app.route("/")
def home():
    """Show the app is working."""
    return "Running!"


@app.route("/pullCompleted", methods=["POST"])
def get_all_finished_local_queue():
    finished_jobs_ids = redis_queue.finished_job_registry.get_job_ids()
    num_of_jobs_to_return = request.args.get("top")
    list_of_jobs_results = get_all_finished_remote_queue()
    for job_id in finished_jobs_ids:
        try:
            job = Job.fetch(job_id, connection=redis_conn)
        except Exception as exception:
            abort(404, description=exception)
        if not job.result:
            abort(
                404,
                description=f"No result found for job_id {job.id}. Try checking the job's status.",
            )
        list_of_jobs_results.append(job.result)
    random_jobs_list = random.sample(list_of_jobs_results, int(num_of_jobs_to_return))
    print(random_jobs_list)
    return jsonify(random_jobs_list)


def get_all_finished_remote_queue():
    remote_redis_host = os.getenv('REMOTE_REDIS_SERVER')
    remote_redis_queue, remote_redis_conn = get_remote_redis_queue_connection(remote_redis_host)
    finished_jobs_ids = remote_redis_queue.finished_job_registry.get_job_ids()
    list_of_all_finished_jobs = []
    for job_id in finished_jobs_ids:
        try:
            job = Job.fetch(job_id, connection=remote_redis_conn)
        except Exception as exception:
            abort(404, description=exception)
        if not job.result:
            abort(
                404,
                description=f"No result found for job_id {job.id}. Try checking the job's status.",
            )
        list_of_all_finished_jobs.append(job.result)
    return list_of_all_finished_jobs


def get_remote_redis_queue_connection(remote_redis_host):
    remote_redis_conn = redis.Redis(
        host=os.getenv("REDIS_HOST", remote_redis_host),
        port=os.getenv("REDIS_PORT", "6379"),
        password=os.getenv("REDIS_PASSWORD", ""),
    )
    redis_queue = Queue(connection=remote_redis_conn)
    return redis_queue, remote_redis_conn


@app.route("/enqueue", methods=["PUT"])
def enqueue():
    if request.method == "PUT":
        num_of_iter = request.args.get("iterations")
        if not num_of_iter:
            abort(
                404,
                description=(
                    "No query parameter iterations passed. "
                    "Send a  int value to the num query parameter."
                ),
            )
        data = request.get_data()
        print(data)
        print(num_of_iter)

    job = redis_queue.enqueue(hash_work, data, int(num_of_iter), result_ttl=86400)
    return jsonify({"job_id": job.id})


# @app.route("/check_status")
def check_status():
    """Takes a job_id and checks its status in redis queue."""
    job_id = request.args["job_id"]

    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception as exception:
        abort(404, description=exception)

    return jsonify({"job_id": job.id, "job_status": job.get_status()})


# @app.route("/get_result")
def get_result():
    """Takes a job_id and returns the job's result."""
    job_id = request.args["job_id"]

    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception as exception:
        abort(404, description=exception)

    if not job.result:
        abort(
            404,
            description=f"No result found for job_id {job.id}. Try checking the job's status.",
        )
    return job.result


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

    print(instances["Instances"][0]["InstanceId"])


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
