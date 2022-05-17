"""The Flask App."""

# pylint: disable=broad-except
import os
from flask import Flask, abort, jsonify, request
from rq.job import Job
import random
import sys

from functions import hash_work
from redis_resc import redis_conn, redis_queue
import redis
from rq import Queue


app = Flask(__name__)


@app.errorhandler(404)
def resource_not_found(exception):
    """Returns exceptions as part of a json."""
    return jsonify(error=str(exception)), 404


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
    remote_redis_host = sys.argv[1]
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
    remote_redis_queue = Queue(connection=remote_redis_conn)
    return remote_redis_queue, remote_redis_conn


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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
