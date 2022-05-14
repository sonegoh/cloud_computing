"""Define functions to use in redis queue."""
import time
import hashlib

from rq import get_current_job


# def some_long_function(some_input):
#     """An example function for redis queue."""
#     job = get_current_job()
#     print("sleeping for 10 sec")
#     time.sleep(10)
#     print("done sleeping")
#
#     return {
#         "job_id": job.id,
#         "job_enqueued_at": job.enqueued_at.isoformat(),
#         "job_started_at": job.started_at.isoformat(),
#         "input": some_input,
#         "result": some_input,
#     }


def hash_work(data_input, iterations):
    job = get_current_job()
    print("sleeping for 5 sec")
    time.sleep(5)
    print("done sleeping")
    print(f"data_input is {data_input}")
    output = ""
    for i in range(iterations - 1):
        output = hashlib.sha512(data_input).digest()
    output = hashlib.sha512(output).digest()
    print(f"output is {output}")
    return job.id, output
