import sys
from . import test_model_ingest
from . import conftest

sys.path.append("lambda/")  # add the lambda directory to path

mem_model_text = test_model_ingest.mem_model_text
mem_model_default_param = test_model_ingest.mem_model_default_param
get_mem_model_file_text = test_model_ingest.get_mem_model_file_text
put_mem_model_file = test_model_ingest.put_mem_model_file


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
    """Test the lambda handler for JobPredict"""
    from calcloud import io

    bucket = conftest.BUCKET
    comm = io.get_io_bundle(bucket=bucket, client=s3_client)
    conftest.setup_dynamodb(dynamodb_client)

    ipst = "ipppssoo0"

    # create and put the memory model file
    mem_model_params = mem_model_default_param.copy()
    put_mem_model_file(ipst, comm, fileparams=mem_model_params)

    # create event for the predict_handler
    key = f"control/{ipst}/{ipst}_MemModelFeatures.txt"
    event = {"Bucket": bucket, "Key": key, "Ipppssoot": ipst}

    # calling predict_handler.lambda_handler directly will fail with OSError: No file or directory found at ./models/mem_clf/
    # use mock_job_predict_lambda_handler defined above instead
    predictions = mock_job_predict_lambda_handler(event, {})
    assert predictions["memBin"] == 0


def test_model_lambda_job_predict_features(s3_client, s3_resource):
    """Test the different mapping options in predict_handler.Preprocessor.scrub_keys()"""
    from JobPredict import predict_handler
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

    mem_model_file_name_1 = f"control/{ipst_1}/{ipst_1}_MemModelFeatures.txt"
    mem_model_file_name_2 = f"control/{ipst_2}/{ipst_2}_MemModelFeatures.txt"

    preprocessor1 = predict_handler.Preprocess(ipst_1, bucket, mem_model_file_name_1)
    preprocessor2 = predict_handler.Preprocess(ipst_2, bucket, mem_model_file_name_2)

    preprocessor1.input_data = preprocessor1.import_data()
    preprocessor2.input_data = preprocessor2.import_data()

    mem_model_features_1 = preprocessor1.scrub_keys()
    mem_model_features_2 = preprocessor2.scrub_keys()

    # the order of scrub_keys() output copied from predict_handler.py
    dict_keys = ["n_files", "total_mb", "drizcorr", "pctecorr", "crsplit", "subarray", "detector", "dtype", "instr"]

    for i in range(len(dict_keys)):
        assert mem_model_features_1[i] == mem_model_expected_dict_1[dict_keys[i]]
        assert mem_model_features_2[i] == mem_model_expected_dict_2[dict_keys[i]]
