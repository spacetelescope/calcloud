from . import conftest
from pprint import pprint
import os
import time

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
    keys = mem_model_text.keys()
    lines = list()
    for key in keys:
        lines.append(f"{mem_model_text[key]}{params[key]}")
    file_text = "\n".join(lines)
    return file_text


def test_model_ingest_mock(s3_client, dynamodb_resource, dynamodb_client):
    from calcloud import io
    from calcloud import model_ingest

    bucket = conftest.BUCKET
    table_name = os.environ.get("DDBTABLE")
    conftest.setup_dynamodb(dynamodb_client)

    comm = io.get_io_bundle(bucket=bucket, client=s3_client)

    ipst = "ipppssoo0"
    n_files = 2
    wallclock_times = ["1:32.79", "0:30.26"]
    memory = ["423876", "236576"]

    # create and put the memory model file
    mem_model_params = mem_model_default_param.copy()
    mem_model_params["n_files"] = n_files
    mem_model_file_text = get_mem_model_file_text(params=mem_model_params)
    mem_model_file_name = f"{ipst}/{ipst}_MemModelFeatures.txt"
    mem_model_file_msg = {mem_model_file_name: mem_model_file_text}
    comm.control.put(mem_model_file_msg)

    # create and put the process metrics file
    process_metrics_params = metrics_default_param.copy()
    process_metrics_params["elapsed_time"] = wallclock_times[0]
    process_metrics_params["max_resident_set_size"] = memory[0]
    process_metrics_file_text = get_metrics_file_text(params=process_metrics_params)
    process_metrics_file_name = f"{ipst}/process_metrics.txt"
    process_metrics_file_msg = {process_metrics_file_name: process_metrics_file_text}
    comm.outputs.put(process_metrics_file_msg)

    # create and put the preview metrics file
    preview_metrics_params = metrics_default_param.copy()
    preview_metrics_params["elapsed_time"] = wallclock_times[1]
    preview_metrics_params["max_resident_set_size"] = memory[1]
    preview_metrics_file_text = get_metrics_file_text(params=preview_metrics_params)
    preview_metrics_file_name = f"{ipst}/preview_metrics.txt"
    preview_metrics_file_msg = {preview_metrics_file_name: preview_metrics_file_text}
    comm.outputs.put(preview_metrics_file_msg)

    model_ingest.ddb_ingest(ipst, bucket, table_name)
