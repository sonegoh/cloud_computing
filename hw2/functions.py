"""Define functions to use in redis queue."""
import time
import hashlib

from rq import get_current_job


def hash_work(data_input, iterations):
    job = get_current_job()
    print("sleeping for 5 sec")
    time.sleep(5)
    print("done sleeping")
    print(f"data_input is {data_input}")
    output = b""
    for i in range(iterations - 1):
        output = hashlib.sha512(output).digest()
    output = hashlib.sha512(output).digest().hex()
    print(f"output is {output}")
    return {"job_id": job.id,
            "output_hash": output}
