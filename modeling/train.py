from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import PowerTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error as MSE
from sklearn.metrics import confusion_matrix
import tensorflow as tf
from tensorflow.keras import Sequential, Model, Input
from tensorflow.keras.layers import Dense
from tensorflow.keras.wrappers.scikit_learn import KerasClassifier, KerasRegressor
from sklearn.model_selection import StratifiedKFold, KFold, cross_val_score
import zipfile
import os
import time
import datetime as dt
import numpy as np
import pandas as pd
import sys
from . import io


""" ----- PREPROCESSING ----- """


def combine_s3_datasets(keys, dropnans=1):
    """Pass in a list of dataframes or local csv filepaths for features, targets and predictions (must be in that order).
    args:
    `keys` (list): [features_df, targets_df, preds_df] or ['features.csv', 'targets.csv', 'preds.csv']
    `dropnans` (default=1)
    0: leave data as is (do not remove NaNs)
    1: drop NaNs from features+targets
    2: drop NaNs from features+targets+preds 
    """
    # load files from csv
    F = pd.read_csv(keys[0], index_col="ipst")
    T = pd.read_csv(keys[1], index_col="ipst")
    P = pd.read_csv(keys[2], index_col="ipst")
    # print data summaries
    print("Features: ", len(F))
    print("Targets: ", len(T))
    print("Preds: ", len(P))
    # combine into single df
    data = F.join(T, how="left")
    if dropnans == 1:
        df0 = data.dropna(axis=0, inplace=False)
        print(f"NaNs Removed: {len(data) - len(df0)}")
        df1 = df0.join(P, how="left")
    elif dropnans == 2:
        df0 = data.join(P, how="left")
        df1 = df0.dropna(axis=0, inplace=False)
        print(f"NaNs Removed: {len(df0) - len(data)}")
    else:
        df1 = data.join(P, how="left")
    print(df1.isna().sum())
    # drop duplicates
    df1["ipst"] = df1.index
    df1.set_index("ipst", inplace=True, drop=False)
    df = df1.drop_duplicates(subset="ipst", keep="last", inplace=False)
    print("Final: ", len(df))
    io.save_dataframe(df, "batch.csv")
    return df


def combine_training_sets(batch, master=None):
    """Takes a list of dataframes and combines them into one
    Removes duplicates and keeps only latest (ordered by df list index)
    """
    if master is None:
        print("Batch data only (skipping Master)")
        return batch
    else:
        df_list = [master, batch]
    n_combined = 0
    for df in df_list:
        n_combined += len(df)
        print("+ ", len(df))
    print("Combined: ", n_combined)
    df_tmp = pd.concat([d for d in df_list], axis=0, verify_integrity=False)
    df_tmp["ipst"] = df_tmp.index
    df_tmp.set_index("ipst", inplace=True, drop=False)
    df = df_tmp.drop_duplicates(subset="ipst", keep="last", inplace=False)
    print(f"Removed {n_combined - len(df)} duplicates")
    print("Final DF: ", len(df))
    return df


def update_power_transform(df):
    pt = PowerTransformer(standardize=False)
    df_cont = df[["n_files", "total_mb"]]
    pt.fit(df_cont)
    input_matrix = pt.transform(df_cont)
    # FILES (n_files)
    f_mean = np.mean(input_matrix[:, 0])
    f_sigma = np.std(input_matrix[:, 0])
    # SIZE (total_mb)
    s_mean = np.mean(input_matrix[:, 1])
    s_sigma = np.std(input_matrix[:, 1])
    files = input_matrix[:, 0]
    size = input_matrix[:, 1]
    x_files = (files - f_mean) / f_sigma
    x_size = (size - s_mean) / s_sigma
    normalized = np.stack([x_files, x_size], axis=1)
    idx = df_cont.index
    df_norm = pd.DataFrame(normalized, index=idx, columns=["x_files", "x_size"])
    df["x_files"] = df_norm["x_files"]
    df["x_size"] = df_norm["x_size"]
    pt_transform = {"lambdas": pt.lambdas_, "f_mean": f_mean, "f_sigma": f_sigma, "s_mean": s_mean, "s_sigma": s_sigma}
    print(pt_transform)
    return df, pt_transform


def preprocess(bucket_mod, prefix, src, table_name, filter):
    # MAKE TRAINING SET - single df for ingested data
    master_data = None # for now only affects s3 data source
    if src == 'ddb': #dynamodb 'calcloud-hst-data'
        ddb_data = io.ddb_download(table_name, filter)
        # write to csv
        io.write_to_csv(ddb_data, 'batch.csv')
    elif src == 's3':
        keys = ['features.csv', 'targets.csv', 'preds.csv']
        io.s3_download(keys, bucket_mod, prefix)
        df = combine_s3_datasets(keys, dropnans=1)
        io.s3_upload(["batch.csv"], bucket_mod, prefix)
        # get previous training data from s3
        try:
            io.s3_download(["master.csv"], bucket_mod, "latest")
            master_data = pd.read_csv("master.csv", index_col="ipst")
        except Exception as e:
            print("Master dataset not found in s3.")
            print(e)
        # combine previous with new data
    df = combine_training_sets(df, master_data)
    # update power transform
    df, pt_transform = update_power_transform(df)
    io.save_dataframe(df, "latest.csv")
    if src == 's3': # save pt metadata and updated dataframe
        keys = io.save_dict({"pt_transform": pt_transform}, "latest.csv")
    else: # (DDB) save just pt metadata
        keys = io.save_dict({"pt_transform": pt_transform})
    io.s3_upload(keys, bucket_mod, prefix)
    return df


""" ----- TRAINING ----- """


def encode_target_data(y_train, y_test):
    # reshape target data
    y_train = y_train.reshape(-1, 1)
    y_test = y_test.reshape(-1, 1)
    # label encode class values as integers
    encoder = LabelEncoder()
    encoder.fit(y_train)
    y_train_enc = encoder.transform(y_train)
    y_train = tf.keras.utils.to_categorical(y_train_enc)
    # test set
    encoder.fit(y_test)
    y_test_enc = encoder.transform(y_test)
    y_test = tf.keras.utils.to_categorical(y_test_enc)
    # ensure train/test targets have correct shape (4 bins)
    print(y_train.shape, y_test.shape)
    return y_train, y_test


def make_tensors(X_train, y_train, X_test, y_test):
    """Convert Arrays to Tensors"""
    X_train = tf.convert_to_tensor(X_train, dtype=tf.float32)
    y_train = tf.convert_to_tensor(y_train, dtype=tf.float32)
    X_test = tf.convert_to_tensor(X_test, dtype=tf.float32)
    y_test = tf.convert_to_tensor(y_test, dtype=tf.float32)
    return X_train, y_train, X_test, y_test


def split_Xy(df, target_col):
    targets = df[target_col]
    cols = ["n_files", "total_mb", "wallclock", "memory", "mem_bin", "mem_pred", "bin_pred", "wall_pred", "ipst"]
    drop_cols = [col for col in cols if col in df.columns]
    features = df.drop(columns=drop_cols, axis=1, inplace=False)
    X = features.values
    y = targets.values
    return X, y


def prep_data(df, target_col, tensors=True):
    # split
    X, y = split_Xy(df, target_col)
    # encode if classifier
    if target_col == "mem_bin":
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y)
        y_train, y_test = encode_target_data(y_train, y_test)
    else:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    if tensors is True:
        # convert arrays into tensors (better performance for tensorflow)
        X_train, y_train, X_test, y_test = make_tensors(X_train, y_train, X_test, y_test)
    return X_train, y_train, X_test, y_test


def get_latest_models(bucket_mod):
    latest_models = []
    io.s3_download(["models.zip"], bucket_mod, "latest")
    os.makedirs("latest", exist_ok=True)
    with zipfile.ZipFile("models.zip", "r") as zip_ref:
        zip_ref.extractall("latest")
    paths = ["mem_clf", "mem_reg", "wall_reg"]
    for path in paths:
        latest = tf.keras.models.load_model(f"latest/models/{path}")
        model = Model(inputs=latest.inputs, outputs=latest.outputs)
        latest_models.append(model)
    clf = latest_models[0]
    clf.compile(loss="categorical_crossentropy", optimizer="adam", metrics=["accuracy"])
    mem_reg = latest_models[1]
    mem_reg.compile(loss="mean_squared_error", optimizer="adam")
    wall_reg = latest_models[2]
    wall_reg.compile(loss="mean_squared_error", optimizer="adam")
    return clf, mem_reg, wall_reg


def memory_classifier(input_shape=9, layers=[18, 32, 64, 32, 18, 9], input_name="hst_jobs", output_name="mem_clf"):
    model = Sequential()
    # visible layer
    inputs = Input(shape=(input_shape,), name=input_name)
    # hidden layers
    x = Dense(layers[0], activation="relu", name=f"1_dense{layers[0]}")(inputs)
    for i, layer in enumerate(layers[1:]):
        i += 1
        x = Dense(layer, activation="relu", name=f"{i+1}_dense{layer}")(x)
    # output layer
    outputs = Dense(4, activation="softmax", name=f"output_{output_name}")(x)
    model = Model(inputs=inputs, outputs=outputs, name="sequential_mlp")
    model.compile(loss="categorical_crossentropy", optimizer="adam", metrics=["accuracy"])
    return model


def memory_regressor(input_shape=9, layers=[18, 32, 64, 32, 18, 9], input_name="hst_jobs", output_name="memory_reg"):
    model = Sequential()
    # visible layer
    inputs = Input(shape=(input_shape,), name=input_name)
    # hidden layers
    x = Dense(layers[0], activation="relu", name="dense_1")(inputs)
    for i, layer in enumerate(layers[1:]):
        i += 1
        x = Dense(layer, activation="relu", name=f"dense_{i+1}")(x)
    # output layer
    outputs = Dense(1, name=output_name)(x)
    model = Model(inputs=inputs, outputs=outputs, name="sequential_mlp")
    model.compile(loss="mean_squared_error", optimizer="adam", metrics=["accuracy"])
    return model


def wallclock_regressor(
    input_shape=9, layers=[18, 32, 64, 128, 256, 128, 64, 32, 18, 9], input_name="hst_jobs", output_name="wallclock_reg"
):
    model = Sequential()
    # visible layer
    inputs = Input(shape=(input_shape,), name=input_name)
    # hidden layers
    x = Dense(layers[0], activation="relu", name="dense_1")(inputs)
    for i, layer in enumerate(layers[1:]):
        i += 1
        x = Dense(layer, activation="relu", name=f"dense_{i+1}")(x)
    # output layer
    outputs = Dense(1, name=output_name)(x)
    model = Model(inputs=inputs, outputs=outputs, name="sequential_mlp")
    model.compile(loss="mean_squared_error", optimizer="adam", metrics=["accuracy"])
    return model


def fit(model, X_train, y_train, X_test, y_test, verbose=1, epochs=60, batch_size=32, callbacks=None):
    # make_batches = batch_maker(batch_size)
    # steps_per_epoch = (X_train.shape[0]//batch_size)
    validation_data = (X_test, y_test)
    t_start = time.time()
    start = dt.datetime.fromtimestamp(t_start).strftime("%m/%d/%Y - %I:%M:%S %p")
    print("\nTRAINING STARTED: ", start)
    history = model.fit(
        X_train,
        y_train,
        batch_size=batch_size,
        validation_data=validation_data,
        verbose=verbose,
        epochs=epochs,
        callbacks=callbacks,
    )
    t_end = time.time()
    end = dt.datetime.fromtimestamp(t_end).strftime("%m/%d/%Y - %I:%M:%S %p")
    print("\nTRAINING COMPLETE: ", end)
    duration = io.proc_time(t_start, t_end)
    print(f"Process took {duration}\n")
    model.summary()
    return history


def save_model(model, name="Sequential", weights=True):
    """The model architecture, and training configuration (including the optimizer, losses, and metrics)
    are stored in saved_model.pb. The weights are saved in the variables/ directory."""
    model_path = os.path.join("models", name)
    weights_path = f"{model_path}/weights/ckpt"
    model.save(model_path)
    if weights is True:
        model.save_weights(weights_path)
    for root, _, files in os.walk(model_path):
        indent = "    " * root.count(os.sep)
        print("{}{}/".format(indent, os.path.basename(root)))
        for filename in files:
            print("{}{}".format(indent + "    ", filename))


""" ----- EVALUATION ----- """


def make_arrays(X_train, y_train, X_test, y_test):
    X_train = np.asarray(X_train, dtype="float32")
    y_train = np.asarray(y_train, dtype="float32")
    X_test = np.asarray(X_test, dtype="float32")
    y_test = np.asarray(y_test, dtype="float32")
    return X_train, y_train, X_test, y_test


def get_scores(model, X_train, y_train, X_test, y_test):
    train_scores = model.evaluate(X_train, y_train, verbose=2)
    test_scores = model.evaluate(X_test, y_test, verbose=2)
    train_acc = np.round(train_scores[1], 2)
    train_loss = np.round(train_scores[0], 2)
    test_acc = np.round(test_scores[1], 2)
    test_loss = np.round(test_scores[0], 2)
    scores = {"train_acc": train_acc, "train_loss": train_loss, "test_acc": test_acc, "test_loss": test_loss}
    return scores


def predict_clf(model, X_train, y_train, X_test, y_test, probas=0):
    proba = model.predict(X_test)
    preds = np.argmax(proba, axis=-1)
    pred_proba = list(zip(preds, np.amax(proba, axis=-1)))
    if probas == 0:  # default
        return preds
    elif probas == 1:
        return pred_proba
    elif probas == 2:
        return preds, proba
    elif probas == 3:
        return proba


def get_preds(X, y, model=None, verbose=0):
    if model is None:
        model = model
    # class predictions
    y_true = np.argmax(y, axis=-1)
    y_pred = np.argmax(model.predict(X), axis=-1)
    preds = pd.Series(y_pred).value_counts(normalize=False)
    pred_norm = pd.Series(y_pred).value_counts(normalize=True)
    if verbose:
        print("y_pred:\n")
        print(preds)
        print(pred_norm)
    return y_true, y_pred


def predict_reg(model, X_train, y_train, X_test, y_test):
    # predict results of training set
    y_hat = model.predict(X_train)
    rmse_train = np.sqrt(MSE(y_train, y_hat))
    print("RMSE Train : % f" % (rmse_train))
    # # predict results of test set
    y_pred = model.predict(X_test)
    # RMSE Computation
    rmse_test = np.sqrt(MSE(y_test, y_pred))
    print("RMSE Test : % f" % (rmse_test))
    # train_preds = np.concatenate((y_pred.reshape(len(y_pred), 1), y_test.reshape(len(y_test), 1)), 1)
    np.set_printoptions(precision=2)
    preds = np.concatenate((y_pred.reshape(len(y_pred), 1), y_test.reshape(len(y_test), 1)), 1)
    return preds


def get_resid(preds):
    res = []
    res_zero = []
    res_over = []
    res_under = []
    for p, a in preds:
        # predicted - actual
        r = p - a
        if r == 0:
            res_zero.append(r)
        if r > 0:
            res_over.append(r)
        else:
            res_under.append(r)
        res.append(r)
    try:
        L2 = np.linalg.norm([p - a for p, a in preds])
        print("Cost (L2 Norm): ", L2)
    except Exception as e:
        print(e)

    print("\n# Exact: ", len(res_zero))
    print("# Overest: ", len(res_over))
    print("# Underest: ", len(res_under))

    print("Overest Avg: ", np.mean(res_over))
    print("Underest Avg: ", np.mean(res_under))
    return res


def evaluate_classifier(model, target_col, X_train, y_train, X_test, y_test, verbose):
    history = fit(model, X_train, y_train, X_test, y_test, verbose=verbose, epochs=60, batch_size=32, callbacks=None)
    scores = get_scores(model, X_train, y_train, X_test, y_test)
    y_true, y_pred = get_preds(X_test, y_test, model, verbose=verbose)
    matrix = confusion_matrix(y_true, y_pred)
    preds, proba = predict_clf(model, X_train, y_train, X_test, y_test, probas=2)
    training_results = {
        "name": target_col,
        "kind": "classifier",
        "scores": scores,
        "preds": preds,
        "proba": proba,
        "y_true": y_true,
        "y_pred": y_pred,
        "matrix": matrix,
        "history": history,
    }
    results_df = pd.DataFrame.from_dict(training_results, orient="index", columns={"Training Results"})
    key = f"{target_col}-results.csv"
    results_df.to_csv(key)
    return key


def evaluate_regressor(model, target_col, X_train, y_train, X_test, y_test, verbose):
    if target_col == "memory":
        history = fit(
            model, X_train, y_train, X_test, y_test, verbose=verbose, epochs=60, batch_size=32, callbacks=None
        )
    elif target_col == "wallclock":
        history = fit(
            model, X_train, y_train, X_test, y_test, verbose=verbose, epochs=300, batch_size=64, callbacks=None
        )
    scores = get_scores(model, X_train, y_train, X_test, y_test)
    X_train, y_train, X_test, y_test = make_arrays(X_train, y_train, X_test, y_test)
    preds = predict_reg(model, X_train, y_train, X_test, y_test)
    res = get_resid(preds)
    training_results = {
        "name": target_col,
        "kind": "regression",
        "scores": scores,
        "predictions": preds,
        "residuals": res,
        "history": history,
    }
    results_df = pd.DataFrame.from_dict(training_results, orient="index", columns={"Training Results"})
    key = f"{target_col}-results.csv"
    results_df.to_csv(key)
    return key


def train_memory_classifier(df, clf, bucket_mod, data_path, verbose):
    target_col = "mem_bin"
    X_train, y_train, X_test, y_test = prep_data(df, target_col, tensors=True)
    if clf is None:
        clf = memory_classifier()
    results_key = evaluate_classifier(clf, target_col, X_train, y_train, X_test, y_test, verbose)
    save_model(clf, name="mem_clf", weights=True)
    io.s3_upload([results_key], bucket_mod, f"{data_path}/results")
    # zip and upload trained model to s3
    io.zip_models("./models/mem_clf", zipname="mem_clf.zip")
    io.s3_upload(["mem_clf.zip"], bucket_mod, f"{data_path}/models")


def train_memory_regressor(df, mem_reg, bucket_mod, data_path, verbose):
    target_col = "memory"
    X_train, y_train, X_test, y_test = prep_data(df, target_col, tensors=True)
    if mem_reg is None:
        mem_reg = memory_regressor()
    results_key = evaluate_regressor(mem_reg, target_col, X_train, y_train, X_test, y_test, verbose)
    save_model(mem_reg, name="mem_reg", weights=True)
    io.s3_upload([results_key], bucket_mod, f"{data_path}/results")
    # zip and upload trained model to s3
    io.zip_models("./models/mem_reg", zipname="mem_reg.zip")
    io.s3_upload(["mem_reg.zip"], bucket_mod, f"{data_path}/models")


def train_wallclock_regressor(df, wall_reg, bucket_mod, data_path, verbose):
    target_col = "wallclock"
    X_train, y_train, X_test, y_test = prep_data(df, target_col, tensors=True)
    if wall_reg is None:
        wall_reg = wallclock_regressor()
    results_key = evaluate_regressor(wall_reg, target_col, X_train, y_train, X_test, y_test, verbose)
    save_model(wall_reg, name="wall_reg", weights=True)
    io.s3_upload([results_key], bucket_mod, f"{data_path}/results")
    # zip and upload trained model to s3
    io.zip_models("./models/wall_reg", zipname="wall_reg.zip")
    io.s3_upload(["wall_reg.zip"], bucket_mod, f"{data_path}/models")


def kfold_cross_val(df, target_col, bucket_mod, data_path, verbose):
    # evaluate using 10-fold cross validation
    print("\nStarting KFOLD Cross-Validation...")
    start = time.time()
    X, y = split_Xy(df, target_col)
    # run estimator
    if target_col == "mem_bin":
        # Y = y.reshape(-1, 1)
        encoder = LabelEncoder()
        y = encoder.fit_transform(y)
        # y_enc = keras.utils.to_categorical(y)
        estimator = KerasClassifier(build_fn=memory_classifier, epochs=30, batch_size=32, verbose=verbose)
        kfold = StratifiedKFold(n_splits=10, shuffle=True)
    elif target_col == "memory":
        estimator = KerasRegressor(build_fn=memory_regressor, epochs=150, batch_size=32, verbose=verbose)
        kfold = KFold(n_splits=10, shuffle=True)
    elif target_col == "wallclock":
        estimator = KerasRegressor(build_fn=wallclock_regressor, epochs=300, batch_size=64, verbose=verbose)
        kfold = KFold(n_splits=10, shuffle=True)
    results = cross_val_score(estimator, X, y, cv=kfold, n_jobs=-1)
    end = time.time()
    duration = io.proc_time(start, end)
    if target_col == "mem_bin":
        score = np.mean(results)
    else:
        score = np.sqrt(np.abs(np.mean(results)))
    print(f"\nKFOLD scores: {results}\n")
    print(f"\nMean Score: {score}\n")
    print("\nProcess took ", duration)
    kfold_dict = {f"kfold_{target_col}": {"results": list(results), "score": score, "time": duration}}
    keys = io.save_dict(kfold_dict)
    io.s3_upload(keys, bucket_mod, f"{data_path}/results")


def run_kfold(df, bucket_mod, data_path, models, verbose):
    for target in models:
        kfold_cross_val(df, target, bucket_mod, data_path, verbose)


def train_models(df, bucket_mod, data_path, opt, mod, verbose):
    if mod == "all":
        models = ["mem_bin", "memory", "wallclock"]
    else:
        models = [mod]
    if opt == "validate":
        run_kfold(df, bucket_mod, data_path, models, verbose)
        return
    elif opt == "update":
        clf, mem_reg, wall_reg = get_latest_models(bucket_mod)
    elif opt == "build":
        clf, mem_reg, wall_reg = None, None, None
    else:
        print(f"Arg {opt} is invalid; use `build` (default), `update` or `validate`.")
    pipeline = {
        "mem_bin": train_memory_classifier(df, clf, bucket_mod, data_path, verbose),
        "memory": train_memory_regressor(df, mem_reg, bucket_mod, data_path, verbose),
        "wallclock": train_wallclock_regressor(df, wall_reg, bucket_mod, data_path, verbose),
    }
    for target in pipeline.keys():
        if target in models:
            pipeline[target]


if __name__ == "__main__":
    args = sys.argv
    options = ["build", "update", "validate"]
    models = ["all", "mem_bin", "memory", "wallclock"]
    if len(args) > 2:
        opt, mod = args[1], args[2]
    elif len(args) == 2:
        opt, mod = args[1], "all"
    else:
        opt, mod = "build", "all"
    if opt not in options:
        print(f"Invalid option arg: {opt}")
        print(f"Options: {options}")
        opt = "build"
    if mod not in models:
        print(f"Invalid model arg: {mod}")
        print(f"Mods: {models}")
        mod = "all"
    print("flags:", [opt, mod])
    bucket_mod = os.environ.get("S3MOD", "calcloud-modeling-sb")
    scrapetime = os.environ.get("SCRAPETIME", "now")  # final log event time
    hr_delta = int(os.environ.get("HRDELTA", 1))  # how far back in time to start
    verbose = os.environ.get("VERBOSE", 0)
    src = os.environ.get("DATASOURCE", "ddb")
    table_name = os.environ.get("DDBTABLE", "calcloud-hst-data")
    filter = os.environ.get("DDBFILTER", None)
    t0, data_path = io.get_paths(scrapetime, hr_delta)
    home = os.path.join(os.getcwd(), data_path)
    prefix = f"{data_path}/data"
    os.makedirs(prefix, exist_ok=True)
    os.chdir(prefix)
    df = preprocess(bucket_mod, prefix, src, table_name, filter)
    os.chdir(home)
    train_models(df, bucket_mod, data_path, opt, mod, verbose)
    io.zip_models("./models", zipname="models.zip")
    io.s3_upload(["models.zip"], bucket_mod, f"{data_path}/models")
