"""This module loads a pre-trained ANN to predict job resource requirements for HST.
# 1 - load job metadata inputs from text file in s3
# 2 - encode strings as int/float values in numpy array 
# 3 - load models and generate predictions
# 4 - return preds as json to parent lambda function
"""
import boto3
import json
import numpy as np
import sklearn
from sklearn.preprocessing import PowerTransformer
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import load_model
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

class Preprocess:
    def __init__(self, ipppssoot, bucket_name, key):
        self.ipppssoot = ipppssoot
        self.bucket_name = bucket_name
        self.key = key
        self.input_data = None
        self.inputs = None
    
    def import_data(self):
        """import job metadata file from s3 bucket
        """
        bucket = s3.Bucket(self.bucket_name)
        obj = bucket.Object(self.key)
        input_data = {}
        body = obj.get()['Body'].read().splitlines()
        for line in body:
            k,v = str(line).strip('b\'').split("=")
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
            if k == 'n_files':
                n_files = int(v)
            if k == 'total_mb':
                total_mb = int(np.round(float(v),0))
            if k == 'DETECTOR':
                if v == 'UVIS' or 'WFC':
                    detector = 1
                else:
                    detector = 0
            if k == 'SUBARRAY':
                if v == 'True':
                    subarray = 1
                else:
                    subarray = 0
            if k == 'DRIZCORR':
                if v == 'PERFORM':
                    drizcorr = 1
                else:
                    drizcorr = 0
            if k == 'PCTECORR':
                if v == 'PERFORM':
                    pctecorr = 1
                else:
                    pctecorr = 0        
            if k == 'CRSPLIT':
                if v == 'NaN':
                    crsplit = 0
                elif v == '1.0':
                    crsplit = 1
                else:
                    crsplit = 2

        i = self.ipppssoot
        # dtype (asn or singleton)
        if i[-1] == '0':
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
        """applies yeo-johnson power transform to first two indices of array (n_files, total_mb) using lambdas, mean and standard deviation calculated for each variable prior to model training

        Returns: X inputs as 2D-array for generating predictions 
        """
        X = self.inputs
        n_files = X[0]
        total_mb = X[1]
        # apply power transformer normalization to continuous vars
        x = np.array([[n_files],[total_mb]]).reshape(1,-1)
        pt = PowerTransformer(standardize=False)
        pt.lambdas_ = np.array([-0.96074766, -0.32299156])
        xt = pt.transform(x)
        # normalization (zero mean, unit variance)
        f_mean, f_sigma  = 0.653480238393804, 0.14693259765350208
        s_mean, s_sigma = 1.1648725537429683, 0.7444473983812471
        x_files = np.round(((xt[0,0] - f_mean) / f_sigma), 5)
        x_size = np.round(((xt[0,1] - s_mean) / s_sigma), 5)
        X = np.array([x_files, x_size, X[2], X[3], X[4], X[5], X[6], X[7], X[8]]).reshape(1,-1)
        return X

def get_model(model_path):
    """Loads pretrained Keras functional model"""
    model = keras.models.load_model(model_path)
    return model

def classifier(model, data):
    """Returns class prediction"""
    # pred_proba = model.predict(data)
    # pred = np.argmax(pred_proba, axis=-1)
    pred = np.argmax(model.predict(data), axis=-1)
    return pred

def regressor(model, data):
    """Returns Regression model prediction"""
    pred = model.predict(data)
    return pred

clf = get_model('./models/mem_clf/1/')
mem_reg = get_model('./models/mem_reg/1/')
wall_reg = get_model('./models/wall_reg/1/')
s3 = boto3.resource("s3")

def lambda_handler(event, context):
    """Predict Resource Allocation requirements for memory (bin and GB estimated value) as well as max execution/wallclock time (seconds).
    Memory Bins: 0: < 2GB, 1: 2-8GB, 2: 8-16GB, 3: >16GB
    """
    #bucket_name = event['Records'][0]['s3']['bucket']['name']
    #key = event['Records'][0]['s3']['object']['key']
    bucket_name = event['Bucket']
    key = event['Key']
    ipppssoot = key.split('/')[-1].split('_')[0]
    prep = Preprocess(ipppssoot, bucket_name, key)
    prep.input_data = prep.import_data()
    prep.inputs = prep.scrub_keys()
    X = prep.transformer()
    # Predict Memory Allocation (bin and value preds)
    membin = int(classifier(clf, X))
    memval = np.round(float(regressor(mem_reg, X)), 2)
    # Predict Wallclock Allocation (execution time in seconds)
    clocktime = np.round(float(regressor(wall_reg, X)), 2)
    print(membin, memval, clocktime)
    return {
        "memBin"  : membin,
        "memVal"  : memval,
        "clockTime" : clocktime
    }
