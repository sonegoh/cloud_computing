"""The Flask App."""

# pylint: disable=broad-except

from flask import Flask, abort, jsonify, request
from rq.job import Job
import random

from functions import hash_work
from redis_resc import redis_conn, redis_queue

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
def get_all_finished():
    finished_jobs_ids = redis_queue.finished_job_registry.get_job_ids()
    num_of_jobs_to_return = request.args.get("top")
    random_jobs_list = random.sample(finished_jobs_ids, int(num_of_jobs_to_return))
    print(random_jobs_list)
    list_of_jobs_results = []
    for job_id in random_jobs_list:
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
    return jsonify(list_of_jobs_results)


@app.route("/enqueue", methods=["PUT"])
def enqueue():
    if request.method == "PUT":
        num_of_iter = request.args.get("iterations")
        if not num_of_iter:
            abort(
                404,
                description=(
                    "No query parameter num passed. "
                    "Send a  int value to the num query parameter."
                ),
            )
        data = request.get_data()
        print(data)
        print(num_of_iter)

    job = redis_queue.enqueue(hash_work, data, int(num_of_iter), result_ttl=86400)
    return jsonify({"job_id": job.id})




@app.route("/check_status")
def check_status():
    """Takes a job_id and checks its status in redis queue."""
    job_id = request.args["job_id"]

    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception as exception:
        abort(404, description=exception)

    return jsonify({"job_id": job.id, "job_status": job.get_status()})


@app.route("/get_result")
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
