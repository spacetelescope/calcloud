"""This module loads a pre-trained ANN to predict job resource requirements for HST.
# 1 - load job metadata inputs from text file in s3
# 2 - encode strings as int/float values in numpy array
# 3 - load models and generate predictions
# 4 - return preds as json to parent lambda function
"""
import boto3
import numpy as np
from sklearn.preprocessing import PowerTransformer
import tensorflow as tf
from botocore.config import Config

# mitigation of potential API rate restrictions (esp for Batch API)
retry_config = Config(retries={"max_attempts": 5, "mode": "standard"})
s3 = boto3.resource("s3", config=retry_config)
client = boto3.client("s3", config=retry_config)


def get_model(model_path):
    """Loads pretrained Keras functional model"""
    model = tf.keras.models.load_model(model_path)
    return model


def classifier(model, data):
    """Returns class prediction"""
    pred_proba = model.predict(data)
    pred = int(np.argmax(pred_proba, axis=-1))
    return pred, pred_proba


def regressor(model, data):
    """Returns Regression model prediction"""
    pred = model.predict(data)
    return pred


class Preprocess:
    def __init__(self, ipppssoot, bucket_name, key):
        self.ipppssoot = ipppssoot
        self.bucket_name = bucket_name
        self.key = key
        self.input_data = None
        self.inputs = None

    def import_data(self):
        """import job metadata file from s3 bucket"""
        bucket = s3.Bucket(self.bucket_name)
        obj = bucket.Object(self.key)
        input_data = {}
        body = obj.get()["Body"].read().splitlines()
        for line in body:
            k, v = str(line).strip("b'").split("=")
            input_data[k] = v
        return input_data

    def scrub_keys(self):
        n_files = 0
        total_mb = 0
        detector = 0
        subarray = 0
        drizcorr = 0
        pctecorr = 0
        crsplit = 0

        for k, v in self.input_data.items():
            if k == "n_files":
                n_files = int(v)
            if k == "total_mb":
                total_mb = int(np.round(float(v), 0))
            if k == "DETECTOR":
                if v in ["UVIS", "WFC"]:
                    detector = 1
                else:
                    detector = 0
            if k == "SUBARRAY":
                if v == "True":
                    subarray = 1
                else:
                    subarray = 0
            if k == "DRIZCORR":
                if v == "PERFORM":
                    drizcorr = 1
                else:
                    drizcorr = 0
            if k == "PCTECORR":
                if v == "PERFORM":
                    pctecorr = 1
                else:
                    pctecorr = 0
            if k == "CRSPLIT":
                if v == "NaN":
                    crsplit = 0
                elif v == "1.0":
                    crsplit = 1
                else:
                    crsplit = 2

        i = self.ipppssoot
        # dtype (asn or singleton)
        if i[-1] == "0":
            dtype = 1
        else:
            dtype = 0
        # instr encoding cols
        if i[0] == "j":
            instr = 0
        elif i[0] == "l":
            instr = 1
        elif i[0] == "o":
            instr = 2
        elif i[0] == "i":
            instr = 3

        inputs = np.array([n_files, total_mb, drizcorr, pctecorr, crsplit, subarray, detector, dtype, instr])
        return inputs

    def transformer(self):
        """applies yeo-johnson power transform to first two indices of array (n_files, total_mb) using lambdas, mean and standard deviation calculated for each variable prior to model training.

        Returns: X inputs as 2D-array for generating predictions
        """
        X = self.inputs
        n_files = X[0]
        total_mb = X[1]
        # apply power transformer normalization to continuous vars
        x = np.array([[n_files], [total_mb]]).reshape(1, -1)
        pt = PowerTransformer(standardize=False)
        pt.lambdas_ = np.array([-1.51, -0.12])
        xt = pt.transform(x)
        # normalization (zero mean, unit variance)
        f_mean, f_sigma = 0.5682815234265285, 0.04222565843608133
        s_mean, s_sigma = 1.6250374589283951, 1.0396138451086632
        x_files = np.round(((xt[0, 0] - f_mean) / f_sigma), 5)
        x_size = np.round(((xt[0, 1] - s_mean) / s_sigma), 5)
        X = np.array([x_files, x_size, X[2], X[3], X[4], X[5], X[6], X[7], X[8]]).reshape(1, -1)
        return X


def lambda_handler(event, context):
    """Predict Resource Allocation requirements for memory (GB) and max execution `kill time` / `wallclock` (seconds) using three pre-trained neural networks. This lambda is invoked from the Job Submit lambda which json.dumps the s3 bucket and key to the file containing job input parameters. The path to the text file in s3 assumes the following format: `control/ipppssoot/ipppssoot_MemModelFeatures.txt`.

    MEMORY BIN: classifier predicts which of 4 memory bins is most likely to be needed to process an HST dataset (ipppssoot) successfully. The probabilities of each bin are output to Cloudwatch logs and the highest bin probability is returned to the Calcloud job submit lambda invoking this one. Bin sizes are as follows:

    Memory Bins:
    0: < 2GB
    1: 2-8GB
    2: 8-16GB
    3: >16GB

    WALLCLOCK REGRESSION: regression generates estimate for specific number of seconds needed to process the dataset using the same input data. This number is then tripled in Calcloud for the sake of creating an extra buffer of overhead in order to prevent larger jobs from being killed unnecessarily.

    MEMORY REGRESSION: A third regression model is used to estimate the actual value of memory needed for the job. This is mainly for the purpose of logging/future analysis and is not currently being used for allocating memory in calcloud jobs.
    """
    bucket_name = event["Bucket"]
    # load models
    clf = get_model("./models/mem_clf/")
    mem_reg = get_model("./models/mem_reg/")
    wall_reg = get_model("./models/wall_reg/")
    key = event["Key"]
    ipppssoot = event["Ipppssoot"]
    prep = Preprocess(ipppssoot, bucket_name, key)
    prep.input_data = prep.import_data()
    prep.inputs = prep.scrub_keys()
    X = prep.transformer()
    # Predict Memory Allocation (bin and value preds)
    membin, pred_proba = classifier(clf, X)
    memval = np.round(float(regressor(mem_reg, X)), 2)
    # Predict Wallclock Allocation (execution time in seconds)
    clocktime = int(regressor(wall_reg, X))
    print(f"ipppssoot: {ipppssoot} keys: {prep.input_data}")
    print(f"ipppssoot: {ipppssoot} features: {prep.inputs}")
    print(f"ipppssoot: {ipppssoot} X: {X}")
    predictions = {"ipppssoot": ipppssoot, "memBin": membin, "memVal": memval, "clockTime": clocktime}
    print(predictions)
    probabilities = {"ipppssoot": ipppssoot, "probabilities": pred_proba}
    print(probabilities)
    return {"memBin": membin, "memVal": memval, "clockTime": clocktime}
