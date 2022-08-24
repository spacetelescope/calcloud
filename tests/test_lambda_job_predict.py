import sys
from . import test_model_ingest
from . import conftest

sys.path.append("lambda/")  # add the lambda directory to path

mem_model_text = test_model_ingest.mem_model_text
mem_model_default_param = test_model_ingest.mem_model_default_param
get_mem_model_file_text = test_model_ingest.get_mem_model_file_text


def mock_job_predict_lambda_handler(event, context):
    # copied from predict_handler.lambda handler
    # modified to use a recognizable path for the memory models (lambda/JobPredict/models/ instead of ./models/)

    from JobPredict import predict_handler
    import numpy as np

    bucket_name = event["Bucket"]
    # load models
    clf = predict_handler.get_model("lambda/JobPredict/models/mem_clf/")
    mem_reg = predict_handler.get_model("lambda/JobPredict/models/mem_reg/")
    wall_reg = predict_handler.get_model("lambda/JobPredict/models/wall_reg/")
    key = event["Key"]
    ipppssoot = event["Ipppssoot"]
    pt_data = predict_handler.load_pt_data("lambda/JobPredict/models/pt_transform")
    print(f"pt_data: {pt_data}")
    prep = predict_handler.Preprocess(ipppssoot, bucket_name, key)
    prep.input_data = prep.import_data()
    prep.inputs = prep.scrub_keys()
    X = prep.transformer(pt_data)
    # Predict Memory Allocation (bin and value preds)
    membin, pred_proba = predict_handler.classifier(clf, X)
    memval = np.round(float(predict_handler.regressor(mem_reg, X)), 2)
    # Predict Wallclock Allocation (execution time in seconds)
    clocktime = int(predict_handler.regressor(wall_reg, X))
    print(f"ipppssoot: {ipppssoot} keys: {prep.input_data}")
    print(f"ipppssoot: {ipppssoot} features: {prep.inputs}")
    print(f"ipppssoot: {ipppssoot} X: {X}")
    predictions = {"ipppssoot": ipppssoot, "memBin": membin, "memVal": memval, "clockTime": clocktime}
    print(predictions)
    probabilities = {"ipppssoot": ipppssoot, "probabilities": pred_proba}
    print(probabilities)
    return {"memBin": membin, "memVal": memval, "clockTime": clocktime}


def test_model_lambda_job_predict(s3_client, dynamodb_client):
    from calcloud import io

    bucket = conftest.BUCKET
    comm = io.get_io_bundle(bucket=bucket, client=s3_client)
    conftest.setup_dynamodb(dynamodb_client)

    ipst = "ipppssoo0"

    # create and put the memory model file
    mem_model_params = mem_model_default_param.copy()
    mem_model_file_text = get_mem_model_file_text(params=mem_model_params)
    mem_model_file_name = f"{ipst}/{ipst}_MemModelFeatures.txt"
    mem_model_file_msg = {mem_model_file_name: mem_model_file_text}
    comm.control.put(mem_model_file_msg)

    # create event for the predict_handler
    key = f"control/{ipst}/{ipst}_MemModelFeatures.txt"
    event = {"Bucket": bucket, "Key": key, "Ipppssoot": ipst}

    # calling predict_handler.lambda_handler directly will fail with OSError: No file or directory found at ./models/mem_clf/
    # use mock_job_predict_lambda_handler defined above instead
    predictions = mock_job_predict_lambda_handler(event, {})
    assert predictions["memBin"] == 0

    """Still missing lines 82, 85, 90, 97, 100, 104, 111, 114, 116, 118
    Lines 165-190 are the lambda handler copied and modified in mock_job_predict_lambda_handler above"""
