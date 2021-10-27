from sklearn.metrics import mean_squared_error as MSE
from sklearn.metrics import confusion_matrix
import tensorflow as tf
from tensorflow.keras import Sequential, Model, Input
from tensorflow.keras.layers import Dense
import zipfile
import os
import time
import datetime as dt
import numpy as np
import pandas as pd
from . import io, prep


""" ----- TRAINING ----- """


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
    model = Model(inputs=inputs, outputs=outputs, name="memory_classifier")
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
    model = Model(inputs=inputs, outputs=outputs, name="memory_regressor")
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
    model = Model(inputs=inputs, outputs=outputs, name="wallclock_regressor")
    model.compile(loss="mean_squared_error", optimizer="adam", metrics=["accuracy"])
    return model


def fit(model, X_train, y_train, X_test, y_test, verbose=1, epochs=60, batch_size=32, callbacks=None):
    # make_batches = batch_maker(batch_size)
    # steps_per_epoch = (X_train.shape[0]//batch_size)
    validation_data = (X_test, y_test)
    t_start = time.time()
    start = dt.datetime.fromtimestamp(t_start).strftime("%m/%d/%Y - %I:%M:%S %p")
    model_name = str(model.name_scope().rstrip("/").upper())
    print(f"\nTRAINING STARTED: {start} ***{model_name}***")
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
    print(f"\nTRAINING COMPLETE: {end} ***{model_name}***")
    duration = io.proc_time(t_start, t_end)
    print(f"Process took {duration}\n")
    model.summary()
    return history, duration


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

    res_dict = {"res": res, "zero": res_zero, "over": res_over, "under": res_under, "L2": L2}

    print("\n# Exact: ", len(res_zero))
    print("# Overest: ", len(res_over))
    print("# Underest: ", len(res_under))

    print("Overest Avg: ", np.mean(res_over))
    print("Underest Avg: ", np.mean(res_under))
    return res_dict


def evaluate_classifier(model, target_col, X_train, y_train, X_test, y_test, verbose):
    history, duration = fit(
        model, X_train, y_train, X_test, y_test, verbose=verbose, epochs=60, batch_size=32, callbacks=None
    )
    scores = get_scores(model, X_train, y_train, X_test, y_test)
    y_true, y_pred = get_preds(X_test, y_test, model, verbose=verbose)
    matrix = confusion_matrix(y_true, y_pred)
    preds, proba = predict_clf(model, X_train, y_train, X_test, y_test, probas=2)
    # save results
    training_results = {
        "scores": scores,
        "preds": preds,
        "proba": proba,
        "y_true": y_true,
        "y_pred": y_pred,
        "matrix": matrix,
        "history": history.history,
        "duration": duration,
    }
    keys = io.save_to_pickle(training_results, target_col=target_col)
    return keys


def evaluate_regressor(model, target_col, X_train, y_train, X_test, y_test, verbose):
    if target_col == "memory":
        history, duration = fit(
            model, X_train, y_train, X_test, y_test, verbose=verbose, epochs=60, batch_size=32, callbacks=None
        )
    elif target_col == "wallclock":
        history, duration = fit(
            model, X_train, y_train, X_test, y_test, verbose=verbose, epochs=300, batch_size=64, callbacks=None
        )
    scores = get_scores(model, X_train, y_train, X_test, y_test)
    X_train, y_train, X_test, y_test = make_arrays(X_train, y_train, X_test, y_test)
    preds = predict_reg(model, X_train, y_train, X_test, y_test)
    res = get_resid(preds)
    training_results = {
        "scores": scores,
        "predictions": preds,
        "residuals": res,
        "history": history.history,
        "duration": duration,
    }
    keys = io.save_to_pickle(training_results, target_col=target_col)
    return keys


def train_memory_classifier(df, clf, bucket_mod, data_path, verbose):
    target_col = "mem_bin"
    X_train, y_train, X_test, y_test = prep.prep_data(df, target_col, tensors=True)
    if clf is None:
        clf = memory_classifier()
    results_keys = evaluate_classifier(clf, target_col, X_train, y_train, X_test, y_test, verbose)
    save_model(clf, name="mem_clf", weights=True)
    io.s3_upload(results_keys, bucket_mod, f"{data_path}/results")
    # zip and upload trained model to s3
    io.zip_models("./models/mem_clf", zipname="mem_clf.zip")
    io.s3_upload(["mem_clf.zip"], bucket_mod, f"{data_path}/models")
    X, _ = prep.split_Xy(df, target_col, keep_index=True)
    y_proba = clf.predict(X)
    y_pred = np.argmax(y_proba, axis=-1)
    bin_preds = pd.DataFrame(y_pred, index=X.index, columns=["bin_pred"])
    return bin_preds


def train_memory_regressor(df, mem_reg, bucket_mod, data_path, verbose):
    target_col = "memory"
    X_train, y_train, X_test, y_test = prep.prep_data(df, target_col, tensors=True)
    if mem_reg is None:
        mem_reg = memory_regressor()
    results_keys = evaluate_regressor(mem_reg, target_col, X_train, y_train, X_test, y_test, verbose)
    save_model(mem_reg, name="mem_reg", weights=True)
    io.s3_upload(results_keys, bucket_mod, f"{data_path}/results")
    # zip and upload trained model to s3
    io.zip_models("./models/mem_reg", zipname="mem_reg.zip")
    io.s3_upload(["mem_reg.zip"], bucket_mod, f"{data_path}/models")
    X, _ = prep.split_Xy(df, target_col, keep_index=True)
    y_pred = mem_reg.predict(X)
    mem_preds = pd.DataFrame(y_pred, index=X.index, columns=["mem_pred"])
    return mem_preds


def train_wallclock_regressor(df, wall_reg, bucket_mod, data_path, verbose):
    target_col = "wallclock"
    X_train, y_train, X_test, y_test = prep.prep_data(df, target_col, tensors=True)
    if wall_reg is None:
        wall_reg = wallclock_regressor()
    results_keys = evaluate_regressor(wall_reg, target_col, X_train, y_train, X_test, y_test, verbose)
    save_model(wall_reg, name="wall_reg", weights=True)
    io.s3_upload(results_keys, bucket_mod, f"{data_path}/results")
    # zip and upload trained model to s3
    io.zip_models("./models/wall_reg", zipname="wall_reg.zip")
    io.s3_upload(["wall_reg.zip"], bucket_mod, f"{data_path}/models")
    X, _ = prep.split_Xy(df, target_col, keep_index=True)
    y_pred = wall_reg.predict(X)
    wall_preds = pd.DataFrame(y_pred, index=X.index, columns=["wall_pred"])
    return wall_preds


def wallclock_stats(df):
    wc_dict = {}
    wc_stats = {}
    wc_preds = list(df["wall_pred"].unique())
    for p in wc_preds:
        wc_dict[p] = {}
        wall = df.loc[df.wall_pred == p]["wallclock"]
        std = np.std(wall)
        wc_dict[p]["wc_mean"] = np.mean(wall)
        wc_dict[p]["wc_std"] = std
        wc_dict[p]["wc_err"] = std / np.sqrt(len(wall))
    for idx, row in df.iterrows():
        wc_stats[idx] = {}
        wp = row["wall_pred"]
        if wp in wc_dict:
            wc_stats[idx]["wc_mean"] = wc_dict[wp]["wc_mean"]
            wc_stats[idx]["wc_std"] = wc_dict[wp]["wc_std"]
            wc_stats[idx]["wc_err"] = wc_dict[wp]["wc_err"]
    df_stats = pd.DataFrame.from_dict(wc_stats, orient="index")
    return df_stats


def train_models(df, bucket_mod, data_path, opt, models, verbose):
    preds = {}
    if opt == "update":
        clf, mem_reg, wall_reg = get_latest_models(bucket_mod)
    else:
        clf, mem_reg, wall_reg = None, None, None
    pipeline = {
        "mem_bin": {"model": clf, "function": train_memory_classifier},
        "memory": {"model": mem_reg, "function": train_memory_regressor},
        "wallclock": {"model": wall_reg, "function": train_wallclock_regressor},
    }
    for target in models:
        M = pipeline[target]["model"]
        preds[target] = pipeline[target]["function"].__call__(df, M, bucket_mod, data_path, verbose)

    cols = ["bin_pred", "mem_pred", "wall_pred", "wc_mean", "wc_std", "wc_err"]
    drop_cols = [col for col in cols if col in df.columns]
    df = df.drop(drop_cols, axis=1)
    df_preds = pd.concat([df, preds["mem_bin"], preds["memory"], preds["wallclock"]], axis=1)
    df_stats = wallclock_stats(df_preds)
    df_new = df_preds.join(df_stats, how="left")
    return df_new
