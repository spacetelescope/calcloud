from . import conftest
import os
import pytest

# Parameters to create the MemModelFeatures.txt, process_metrics.txt, and preview_metrics.txt files
metrics_text = {
    "command": 'Command being timed: "python -m caldp.create_previews s3://calcloud-processing-moto/inputs s3://calcloud-processing-moto/outputs/',
    "user_time": "User time (seconds): ",
    "system_time": "System time (seconds): ",
    "percent_cpu": "Percent of CPU this job got: ",
    "elapsed_time": "Elapsed (wall clock) time (h:mm:ss or m:ss): ",
    "avg_shared_text_size": "Average shared text size (kbytes): ",
    "avg_unshared_text_size": "Average unshared data size (kbytes): ",
    "avg_stack_size": "Average stack size (kbytes): ",
    "avg_total_size": "Average total size (kbytes): ",
    "max_resident_set_size": "Maximum resident set size (kbytes): ",
    "avg_resident_set_size": "Average resident set size (kbytes): ",
    "major_page_faults": "Major (requiring I/O) page faults: ",
    "minor_page_faults": "Minor (reclaiming a frame) page faults: ",
    "voluntary_context_switches": "Voluntary context switches: ",
    "involuntary_context_switches": "Involuntary context switches: ",
    "swaps": "Swaps: ",
    "file_system_inputs": "File system inputs: ",
    "file_system_outputs": "File system outputs: ",
    "socket_messages_sent": "Socket messages sent: ",
    "socket_messages_received": "Socket messages received: ",
    "signals_delivered": "Signals delivered: ",
    "page_size": "Page size (bytes): ",
    "exit_status": "Exit status: ",
}

metrics_default_param = {
    "command": "ipppssoot",
    "user_time": "30.0",
    "system_time": "15.0",
    "percent_cpu": "100",
    "elapsed_time": "1:00:00",
    "avg_shared_text_size": "0",
    "avg_unshared_text_size": "0",
    "avg_stack_size": "0",
    "avg_total_size": "0",
    "max_resident_set_size": "1000",
    "avg_resident_set_size": "0",
    "major_page_faults": "0",
    "minor_page_faults": "100",
    "voluntary_context_switches": "100",
    "involuntary_context_switches": "100",
    "swaps": "0",
    "file_system_inputs": "0",
    "file_system_outputs": "2000",
    "socket_messages_sent": "0",
    "socket_messages_received": "0",
    "signals_delivered": "0",
    "page_size": "1000",
    "exit_status": "0",
}

mem_model_text = {
    "n_files": "n_files=",
    "total_mb": "total_mb=",
    "detector": "DETECTOR=",
    "subarray": "SUBARRAY=",
    "drizcorr": "DRIZCORR=",
    "pctecorr": "PCTECORR=",
    "crsplit": "CRSPLIT=",
}

mem_model_default_param = {
    "n_files": "1",
    "total_mb": "10.0",
    "detector": "UVIS",
    "subarray": "False",
    "drizcorr": "OMIT",
    "pctecorr": "PERFORM",
    "crsplit": "1",
}


def get_metrics_file_text(params=metrics_default_param):
    assert sorted(metrics_text.keys()) == sorted(params.keys())
    keys = metrics_text.keys()
    lines = list()
    for key in keys:
        if key == "command":
            lines.append(f'{metrics_text[key]}{params[key]} {params[key]}"')
        elif key == "percent_cpu":
            lines.append(f"{metrics_text[key]}{params[key]}%")
        else:
            lines.append(f"{metrics_text[key]}{params[key]}")
    file_text = "\n".join(lines)
    return file_text


def get_mem_model_file_text(params=mem_model_default_param):
    assert sorted(mem_model_text.keys()) == sorted(params.keys())
    keys = mem_model_text.keys()
    lines = list()
    for key in keys:
        lines.append(f"{mem_model_text[key]}{params[key]}")
    file_text = "\n".join(lines)
    return file_text


def put_preview_metrics_file(ipst, comm, fileparams=metrics_default_param.copy()):
    # create and put the preview metrics file
    preview_metrics_file_text = get_metrics_file_text(params=fileparams)
    preview_metrics_file_name = f"{ipst}/preview_metrics.txt"
    preview_metrics_file_msg = {preview_metrics_file_name: preview_metrics_file_text}
    comm.outputs.put(preview_metrics_file_msg)


def put_process_metrics_file(ipst, comm, fileparams=metrics_default_param.copy()):
    # create and put the process metrics file
    process_metrics_file_text = get_metrics_file_text(params=fileparams)
    process_metrics_file_name = f"{ipst}/process_metrics.txt"
    process_metrics_file_msg = {process_metrics_file_name: process_metrics_file_text}
    comm.outputs.put(process_metrics_file_msg)


def put_mem_model_file(ipst, comm, fileparams=mem_model_default_param.copy()):
    # create and put the memory model file
    mem_model_file_text = get_mem_model_file_text(params=fileparams)
    mem_model_file_name = f"{ipst}/{ipst}_MemModelFeatures.txt"
    mem_model_file_msg = {mem_model_file_name: mem_model_file_text}
    comm.control.put(mem_model_file_msg)


def test_model_ingest_mock(s3_client, dynamodb_resource, dynamodb_client):
    """Test calcloud/model_ingest.py"""
    from calcloud import io
    from calcloud import model_ingest

    bucket = conftest.BUCKET
    table_name = os.environ.get("DDBTABLE")
    conftest.setup_dynamodb(dynamodb_client)

    comm = io.get_io_bundle(bucket=bucket, client=s3_client)

    ipst = "ipppssoo0"
    n_files = 5
    wallclock_times = ["1:32.79", "0:30.26"]
    memory = ["423876", "236576"]

    # create and put the memory model file
    mem_model_params = mem_model_default_param.copy()
    mem_model_params["n_files"] = n_files
    put_mem_model_file(ipst, comm, fileparams=mem_model_params)

    # create and put the process metrics file
    process_metrics_params = metrics_default_param.copy()
    process_metrics_params["elapsed_time"] = wallclock_times[0]
    process_metrics_params["max_resident_set_size"] = memory[0]
    put_process_metrics_file(ipst, comm, fileparams=process_metrics_params)

    # create and put the preview metrics file
    preview_metrics_params = metrics_default_param.copy()
    preview_metrics_params["elapsed_time"] = wallclock_times[1]
    preview_metrics_params["max_resident_set_size"] = memory[1]
    put_preview_metrics_file(ipst, comm, fileparams=preview_metrics_params)

    # call model ingest to scrape the info it needs from these files and put them in dynamodb
    model_ingest.ddb_ingest(ipst, bucket, table_name)

    # get the entry from dynamodb and check that the number of files and total memory is the same as the input
    table = dynamodb_resource.Table(table_name)
    response = table.get_item(Key={"ipst": ipst})["Item"]
    assert response["n_files"] == n_files
    assert float(response["memory"]) == (float(memory[0]) + float(memory[1])) / 1.0e6


def test_model_ingest_no_mem_features(s3_resource):
    from calcloud import model_ingest

    bucket = conftest.BUCKET
    s3_resource.create_bucket(Bucket=bucket)
    ipst = "ipppssoo0"

    feature_scraper = model_ingest.Features(ipst, s3_resource.Bucket(bucket))

    with pytest.raises(SystemExit):
        # attempt to memory model file from an empty s3 bucket
        # since the memory model file does not exist, it should result in an exception and cause the system to exit
        feature_scraper.download_inputs()


def test_model_ingest_target_data_errors(s3_client, s3_resource):
    from calcloud import model_ingest
    from calcloud import io

    bucket = conftest.BUCKET
    s3_resource.create_bucket(Bucket=bucket)
    comm = io.get_io_bundle(bucket=bucket, client=s3_client)
    ipst = "ipppssoo0"

    target_scraper = model_ingest.Targets(ipst, s3_resource.Bucket(bucket))

    with pytest.raises(SystemExit):
        # attempt to retrieve metric files from an empty s3 bucket
        # since the metric files do not exist, it should result in an exception and cause the system to exit
        target_scraper.get_target_data()

    # put metrics files with a non-zero exit status
    preview_fileparams = metrics_default_param.copy()
    process_fileparams = metrics_default_param.copy()
    process_fileparams["exit_status"] = "1"
    put_preview_metrics_file(ipst, comm, fileparams=preview_fileparams)
    put_process_metrics_file(ipst, comm, fileparams=process_fileparams)

    with pytest.raises(SystemExit):
        # since the process metrics file has non-zero exit status, it should result in an exception and cause the system to exit
        target_scraper.get_target_data()


def test_model_ingest_memory_bins(s3_resource):
    from calcloud import model_ingest

    bucket = conftest.BUCKET
    s3_resource.create_bucket(Bucket=bucket)
    ipst = "ipppssoo0"

    target_scraper = model_ingest.Targets(ipst, s3_resource.Bucket(bucket))

    memory_bins = {"memory": [1, 5, 10, 20], "expected_mem_bin": [0, 1, 2, 3]}

    for i in range(len(memory_bins["memory"])):
        mem_bin = target_scraper.calculate_bin(memory_bins["memory"][i])
        assert mem_bin == memory_bins["expected_mem_bin"][i]


def test_model_ingest_feature_dict(s3_client, s3_resource):
    from calcloud import model_ingest
    from calcloud import io

    bucket = conftest.BUCKET
    s3_resource.create_bucket(Bucket=bucket)
    comm = io.get_io_bundle(bucket=bucket, client=s3_client)

    ipst_1 = "ipppssoo0"
    ipst_2 = "jpppssoo1"

    mem_model_param_1 = {
        "n_files": "1",
        "total_mb": "10.0",
        "detector": "UVIS",
        "subarray": "False",
        "drizcorr": "OMIT",
        "pctecorr": "OMIT",
        "crsplit": "1",
    }

    mem_model_param_2 = {
        "n_files": "5",
        "total_mb": "50.0",
        "detector": "CCD",
        "subarray": "True",
        "drizcorr": "PERFORM",
        "pctecorr": "PERFORM",
        "crsplit": "2",
    }

    mem_model_expected_dict_1 = {
        "n_files": 1,
        "total_mb": 10,
        "detector": 1,
        "subarray": 0,
        "drizcorr": 0,
        "pctecorr": 0,
        "crsplit": 1,
        "dtype": 1,
        "instr": 3,
    }

    mem_model_expected_dict_2 = {
        "n_files": 5,
        "total_mb": 50,
        "detector": 0,
        "subarray": 1,
        "drizcorr": 1,
        "pctecorr": 1,
        "crsplit": 2,
        "dtype": 0,
        "instr": 0,
    }

    put_mem_model_file(ipst_1, comm, fileparams=mem_model_param_1)
    put_mem_model_file(ipst_2, comm, fileparams=mem_model_param_2)

    feature_scraper_1 = model_ingest.Features(ipst_1, s3_resource.Bucket(bucket))
    feature_scraper_2 = model_ingest.Features(ipst_2, s3_resource.Bucket(bucket))

    mem_feature_dict_1 = feature_scraper_1.scrape_features()
    mem_feature_dict_2 = feature_scraper_2.scrape_features()

    dict_keys = list(mem_model_expected_dict_1.keys())

    for i in range(len(dict_keys)):
        assert mem_feature_dict_1[dict_keys[i]] == mem_model_expected_dict_1[dict_keys[i]]
        assert mem_feature_dict_2[dict_keys[i]] == mem_model_expected_dict_2[dict_keys[i]]
