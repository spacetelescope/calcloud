import os

job_base = './hstcal-jobs'

with open('./example_datasets.list', "r") as f:
    datasets = f.readlines()

datasets = [i.strip().lower() for i in datasets]

cwd = os.getcwd()

for d in datasets:
    jobdir = f"./{job_base}/{d}"
    os.chdir(jobdir)
    cmd = f"condor_submit_dag DAG-{d}.dag"
    # print(os.getcwd())
    # print(cmd)
    os.system(cmd)
    os.chdir(cwd)