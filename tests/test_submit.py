from calcloud import hst
from . import conftest
import os

IPPPSSOOT_INSTR = hst.IPPPSSOOT_INSTR
instr_keys = list(IPPPSSOOT_INSTR.keys())


def test_submit_plans(s3_client, lambda_client, iam_client, dynamodb_client, batch_client):
    """Test plan.submit_plans() from plan.py.
    Creates a test plan file and submits the jobs in the file"""
    from calcloud import submit
    from calcloud import plan
    from calcloud import io
    from calcloud import batch

    bucket = conftest.BUCKET
    conftest.create_mock_lambda(lambda_client, iam_client)  # create a mock job_predict lambda
    conftest.setup_dynamodb(dynamodb_client)
    conftest.setup_batch(iam_client, batch_client, busybox_sleep_timer=30)  # set up batch

    # a test plan file
    test_plan_file = "test_plan_file"
    current_directory = os.getcwd()
    planfilepath = os.path.join(current_directory, test_plan_file)

    n_plans = 5  # number of lines in plan file, pick a number between 1 and 10
    ipsts = [f"{instr_keys[i].lower()}pppssoo{str(i)}" for i in range(n_plans)]

    # for each ipppssoot, get the default metadata, assign the job_id, retrieve plan and write a line to test_plan_file
    with open(planfilepath, "w") as fp:
        for ipst in ipsts:
            metadata = io.get_default_metadata()
            metadata["job_id"] = ipst
            job_plan = plan.get_plan(ipst, bucket, f"{bucket}/inputs", metadata)
            job_plan_list = list(job_plan)

            for i in range(len(job_plan_list)):
                # add quotation marks to strings
                if isinstance(job_plan_list[i], str):
                    job_plan_list[i] = f"'{job_plan_list[i]}'"

            job_plan_list = [str(i) for i in job_plan_list]  # convert all items to string
            job_plan_line = f"{', '.join(list(job_plan_list))}\n"
            fp.write(job_plan_line)

    # submit the plan file
    submit.submit_plans(planfilepath)

    # get the job names from batch
    job_names = list()
    job_ids = batch.get_job_ids()
    for id in job_ids:
        job_names.append(batch.get_job_name(id))

    # assert that the return jobs names are the same as the ipppssoots submitted from the plan file
    assert sorted(job_names) == sorted(ipsts)

    # remove test_plan_file
    os.remove(planfilepath)