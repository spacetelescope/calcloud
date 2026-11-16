from . import conftest
import os
import pytest

# Parameters to create the MemModelFeatures.txt, process_metrics.txt, and preview_metrics.txt files
metrics_text = {
    "command": 'Command being timed: "python3.11 -m caldp.create_previews s3://calcloud-processing-moto/inputs s3://calcloud-processing-moto/outputs/',
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


@pytest.fixture
def disk_metrics_mixed_df_bg_text():
    return "\n".join(
        [
            "Filesystem     1G-blocks  Used Available Use% Mounted on",
            "overlay              250G   18G      232G   8% /",
            "tmpfs                  1G    0G        1G   0% /dev",
            "overlay              250G  NAG      232G   8% /",  # non-numeric used value
            "overlay              250G   42G      208G  17% /data",
            "overlay              250G",  # partial line
            "missing              cols   10G        2G",  # partial line
            "",
        ]
    )


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


def put_disk_metrics_file(ipst, comm, file_text):
    disk_metrics_file_name = f"{ipst}/disk_metrics.txt"
    disk_metrics_file_msg = {disk_metrics_file_name: file_text}
    comm.outputs.put(disk_metrics_file_msg)


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

    # attempt to memory model file from an empty s3 bucket
    # since the memory model file does not exist, it should get None
    result = feature_scraper.download_inputs()
    assert result is None


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


def test_model_ingest_disk_metrics_max_used_value_in_payload(s3_client, s3_resource, disk_metrics_mixed_df_bg_text):
    from calcloud import model_ingest
    from calcloud import io

    bucket = conftest.BUCKET
    s3_resource.create_bucket(Bucket=bucket)
    comm = io.get_io_bundle(bucket=bucket, client=s3_client)
    ipst = "ipppssoo0"

    put_process_metrics_file(ipst, comm, fileparams=metrics_default_param.copy())
    put_preview_metrics_file(ipst, comm, fileparams=metrics_default_param.copy())
    put_disk_metrics_file(ipst, comm, file_text=disk_metrics_mixed_df_bg_text)

    target_scraper = model_ingest.Targets(ipst, s3_resource.Bucket(bucket))
    target_data = target_scraper.get_target_data()
    assert target_data["max_disk"] == 42

    target_scraper.target_data = target_data
    targets = target_scraper.convert_target_data()

    payload = model_ingest.create_payload(
        {
            "ipst": ipst,
            "features": {"total_mb": 10, "n_files": 1, "dataset_type": "ipst"},
            "targets": targets,
        },
        1.0,
    )

    assert payload["max_disk"] == 42


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
        "dataset_type": "ipst",
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
        "dataset_type": "ipst",
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

    targets = {"memory": 0.5, "wallclock": 10, "mem_bin": 0}
    payload_1 = model_ingest.create_payload({"ipst": ipst_1, "features": mem_feature_dict_1, "targets": targets}, 1.0)
    payload_2 = model_ingest.create_payload({"ipst": ipst_2, "features": mem_feature_dict_2, "targets": targets}, 1.0)

    assert payload_1["dataset_type"] == "ipst"
    assert payload_2["dataset_type"] == "ipst"


def test_model_ingest_feature_dict_svm_missing_values(s3_client, s3_resource):
    from calcloud import io
    from calcloud import model_ingest

    bucket = conftest.BUCKET
    s3_resource.create_bucket(Bucket=bucket)
    comm = io.get_io_bundle(bucket=bucket, client=s3_client)

    svm_dataset = "wfc3_epo_2h"

    # Intentionally omit optional feature keys to verify default handling.
    comm.control.put({f"{svm_dataset}/{svm_dataset}_MemModelFeatures.txt": "n_files=3\ntotal_mb=21.7"})

    svm_features = model_ingest.Features(svm_dataset, s3_resource.Bucket(bucket)).scrape_features()

    svm_expected_dict = {
        "n_files": 3,
        "total_mb": 22,
        "detector": 0,
        "instr": 3,
        "dataset_type": "svm",
    }

    dict_keys = list(svm_expected_dict.keys())
    for i in range(len(dict_keys)):
        assert svm_features[dict_keys[i]] == svm_expected_dict[dict_keys[i]]
    assert "dtype" not in svm_features

    targets = {"memory": 0.5, "wallclock": 10, "mem_bin": 0}
    svm_payload = model_ingest.create_payload({"ipst": svm_dataset, "features": svm_features, "targets": targets}, 1.0)

    assert svm_payload["dataset_type"] == "svm"


def test_model_ingest_feature_dict_mvm_missing_values(s3_client, s3_resource):
    from calcloud import io
    from calcloud import model_ingest

    bucket = conftest.BUCKET
    s3_resource.create_bucket(Bucket=bucket)
    comm = io.get_io_bundle(bucket=bucket, client=s3_client)

    mvm_dataset = "skycell-p0115x10y10"

    # Intentionally omit optional feature keys to verify default handling.
    comm.control.put({f"{mvm_dataset}/{mvm_dataset}_MemModelFeatures.txt": "n_files=9"})

    mvm_features = model_ingest.Features(mvm_dataset, s3_resource.Bucket(bucket)).scrape_features()

    mvm_expected_dict = {
        "n_files": 9,
        "total_mb": 0,
        "dataset_type": "mvm",
    }

    dict_keys = list(mvm_expected_dict.keys())
    for i in range(len(dict_keys)):
        assert mvm_features[dict_keys[i]] == mvm_expected_dict[dict_keys[i]]
    assert "instr" not in mvm_features

    targets = {"memory": 0.5, "wallclock": 10, "mem_bin": 0}
    mvm_payload = model_ingest.create_payload({"ipst": mvm_dataset, "features": mvm_features, "targets": targets}, 1.0)

    assert mvm_payload["dataset_type"] == "mvm"


def test_scrape_job_data_sets_store_data_from_dataset_type_and_raw_field(s3_client, s3_resource):
    from calcloud import io
    from calcloud import model_ingest

    bucket = conftest.BUCKET
    s3_resource.create_bucket(Bucket=bucket)
    comm = io.get_io_bundle(bucket=bucket, client=s3_client)

    dataset_with_field = "wfc3_epo_2h"
    dataset_without_field = "skycell-p0115x10y10"

    comm.control.put(
        {
            f"{dataset_with_field}/{dataset_with_field}_MemModelFeatures.txt": "n_files=3\ntotal_mb=21.7\ndataset_type=svm"
        }
    )
    comm.control.put(
        {f"{dataset_without_field}/{dataset_without_field}_MemModelFeatures.txt": "n_files=9\ntotal_mb=1.1"}
    )

    put_process_metrics_file(dataset_with_field, comm, fileparams=metrics_default_param.copy())
    put_preview_metrics_file(dataset_with_field, comm, fileparams=metrics_default_param.copy())
    put_process_metrics_file(dataset_without_field, comm, fileparams=metrics_default_param.copy())
    put_preview_metrics_file(dataset_without_field, comm, fileparams=metrics_default_param.copy())

    with_field_job_data = model_ingest.Scraper(dataset_with_field, bucket).scrape_job_data()
    without_field_job_data = model_ingest.Scraper(dataset_without_field, bucket).scrape_job_data()

    assert with_field_job_data["store_data"] is True
    assert without_field_job_data["store_data"] is False


def test_ddb_ingest_svm_requires_raw_dataset_type_field(s3_client, s3_resource, dynamodb_resource, dynamodb_client):
    from calcloud import io
    from calcloud import model_ingest

    bucket = conftest.BUCKET
    table_name = os.environ.get("DDBTABLE")
    s3_resource.create_bucket(Bucket=bucket)
    conftest.setup_dynamodb(dynamodb_client)
    comm = io.get_io_bundle(bucket=bucket, client=s3_client)

    svm_dataset = "wfc3_epo_2h"

    # Intentionally omit dataset_type from raw feature text; transition guard should skip ingest.
    comm.control.put({f"{svm_dataset}/{svm_dataset}_MemModelFeatures.txt": "n_files=3\ntotal_mb=21.7"})

    put_process_metrics_file(svm_dataset, comm, fileparams=metrics_default_param.copy())
    put_preview_metrics_file(svm_dataset, comm, fileparams=metrics_default_param.copy())

    model_ingest.ddb_ingest(svm_dataset, bucket, table_name)

    table = dynamodb_resource.Table(table_name)
    response = table.get_item(Key={"ipst": svm_dataset})
    assert "Item" not in response
