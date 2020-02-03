import sys

import boto3

JOB_QUEUE = "hstdp-batch-queue"
# JOB_DEFINITION = "hstdp-ipppssoot-job-dev"
JOB_DEFINITION = "hstdp-ipppssoot-job"

# One key function of JOB_DEFINITION appears to be indelible declaration of Docker image.
# New image == new definition required.

def submit_job(plan, job_definition, job_queue):
    """Given a job description tuple `plan` from the planner,  submit a job to AWS batch."""
    bucket, job_name, ipppssoot, instrument, command, vcpus, memory, seconds = plan
    client = boto3.client("batch")
    job = {
        "jobName": job_name.replace("/","-"),
        "jobQueue": job_queue,
        "jobDefinition": job_definition,
        "containerOverrides": {
            "vcpus": vcpus,
            "memory": memory,
            "command": [
                command,
                bucket,
                job_name,
                ipppssoot
            ],
        },
        "timeout": {
            "attemptDurationSeconds": seconds,
        },
    }
    print("-----", job)
    return client.submit_job(**job)


def main(plan_file, job_definition=JOB_DEFINITION, job_queue=JOB_QUEUE):
    """Given a file `plan_file` defining job plan tuples one-per-line,  
    submit each job and output the plan and submission response to stdout.
    """
    with open(plan_file) as f:
        for line in f.readlines():
            job_plan = eval(line)
            print(submit_job(job_plan, job_definition, job_queue))

if __name__ == "__main__":
    if len(sys.argv) == 2:
        plan_file = sys.argv[1]
        main(plan_file)
    elif len(sys.argv) == 3:
        plan_file = sys.argv[1]
        job_definition = sys.argv[2]
        main(plan_file, job_definition)
    elif len(sys.argv) == 4:
        plan_file = sys.argv[1]
        job_definition = sys.argv[2]
        job_queue = sys.argv[3]
        main(plan_file, job_definition, job_queue)
    else:
        print("usage:  python -m hstdputils.submit <plan_file>  [<job_definition>]  [job_queue]", file=sys.stderr)
