import sys
import pprint
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.amazon.aws.operators.batch import AwsBatchOperator

DEFAULT_QUEUE = "hstdp-batch-queue"
# DEFAULT_JOB_DEFINITION = "hstdp-ipppssoot-job"
DEFAULT_JOB_DEFINITION = "hstdp-ipppssoot-job-dev"
DEFAULT_AIRFLOW_EMAIL = "jmiller@stsci.edu"       
DEFAULT_RETRY_COUNT = 1
DEFAULT_RETRY_MINUTES = 1

def get_operator_pars(job_queue, job_definition, plan):
    bucket, batch_name, ipppssoot, instrument, command, vcpus, memory, seconds = plan
    batch_operator_pars = {
        "job_name": batch_name.replace("/","-"),
        "job_queue": job_queue,
        "job_definition": job_definition,
        "overrides": {
            "vcpus": vcpus,
            "memory": memory,
            "command": [
                command,
                bucket,
                batch_name,
                ipppssoot
            ],
        }
    }
    # "timeout": {
    #     "attemptDurationSeconds": seconds,     # XXXXX IMPORTANT: where is kill time?
    # },
    return batch_operator_pars

def get_default_dag_args(
            email=DEFAULT_AIRFLOW_EMAIL,
            retry_count=DEFAULT_RETRY_COUNT,
            retry_minutes=DEFAULT_RETRY_MINUTES):
    default_args = {
        'owner': 'Airflow',
        'depends_on_past': False,
        'start_date': datetime(1900,1,1,0,0,0),
        'catchup' False,
        'email': email,
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': retry_count,
        'retry_delay': timedelta(minutes=retry_minutes),
        'schedule_interval' : '@once',
        # 'queue': 'bash_queue',
        # 'pool': 'backfill',
        # 'priority_weight': 10,
        # 'end_date': datetime(2016, 1, 1),
    }
    return default_args

def get_airflow_objs(plan, queue=DEFAULT_QUEUE, job_definition=DEFAULT_JOB_DEFINITION, dag_defaults=None):
    pars = get_operator_pars(queue, job_definition, plan)
    dag = DAG(pars["job_name"], default_args=dag_defaults or get_default_dag_args())
    operator = AwsBatchOperator(**pars, dag=dag, task_id=pars["job_name"])
    return pars, dag, operator

'''
def generate_dag_file(plan_file, job_queue, job_definition):
        with open(plan_file) as plans:
            default_dag_args = get_default_dag_args()
            output_text += """
            dagfile_template = f"""
DEFAULT_DAG_ARGS = {pprint.pformat(get_default_dag_args())}

dag = DAG()
"""
            print(DAGFILE_TEMPLATE)
        
def main(plan_file):
    """Given a file `plan_file` defining job plan tuples one-per-line,  
    submit each job and output the plan and submission response to stdout.
    """
    with open(plan_file) as f:
        for line in f.readlines():
            job_plan = eval(line)
            print("----", job_plan)
            print(generate_dag_file(job_plan))
'''

if __name__ == "__main__":
    main(sys.argv[1])
