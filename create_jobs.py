import os
import shutil

job_base = './hstcal-jobs'

inst_map = {
    "j":"acs",
    "i":"wfc3",
    "o":"stis",
    "l":"cos"
}

def mk_or_rep_dir(directory):
    try:
        os.mkdir(directory)
    except OSError:
        shutil.rmtree(directory)
        os.mkdir(directory)

def mk_parent_job(dataset):
    shutil.copy('./scripts/take_a_rest.sh', f"{job_base}/{dataset}/")
    jobfile = f"{job_base}/{dataset}/parent-{dataset}.job"
    with open(jobfile, "w") as job:
        job.write(f"""
Executable=/bin/bash
Arguments=take_a_rest.sh parent

Universe=vanilla
Log=parent_{dataset}.condor_log
+Out = "ALOG_parent_{dataset}.out"
+Err = "ALOG_parent_{dataset}.err"
+Instances=1
getenv=True
transfer_executable=false
transfer_input_files=take_a_rest.sh
Notification=Never
Queue
""")	
    return None

def mk_cal_job(dataset):
    inst = inst_map[dataset[0]]
    shutil.copy(f"./scripts/cal{inst}_wrapper.sh", f"{job_base}/{dataset}/")
    shutil.copy(f"./scripts/retrieve_data.py", f"{job_base}/{dataset}/")
    jobfile = f"{job_base}/{dataset}/calib-{dataset}.job"
    with open(jobfile, "w") as job:
        job.write(f"""
Executable=/bin/bash
Arguments=cal{inst}_wrapper.sh {dataset}
Universe=vanilla
Log=calib_{dataset}.condor_log
+Out = "ALOG_calib_{dataset}.out"
+Err = "ALOG_calib_{dataset}.err"
+Instances=1
getenv=True
transfer_executable=false
transfer_input_files=cal{inst}_wrapper.sh,retrieve_data.py
Notification=Never
Queue  
""")
    return None

def mk_dag(dataset):
    dagfile = f"{job_base}/{dataset}/DAG-{dataset}.dag"
    with open(dagfile, "w") as dag:
        dag.write(f"""
JOB INITIAL parent-{dataset}.job
JOB CALIBRATE calib-{dataset}.job

PARENT INITIAL CHILD CALIBRATE

PRIORITY INITIAL 120
PRIORITY CALIBRATE 121
""")
    return None


mk_or_rep_dir(job_base)

with open('./example_datasets.list', "r") as f:
    datasets = f.readlines()

datasets = [i.strip().lower() for i in datasets]

for d in datasets:
    jobdir = f"./{job_base}/{d}"
    mk_or_rep_dir(jobdir)

    mk_parent_job(d)
    mk_cal_job(d)
    mk_dag(d)
    

    
