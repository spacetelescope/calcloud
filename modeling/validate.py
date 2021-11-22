import time
import numpy as np
from tensorflow.keras.wrappers.scikit_learn import KerasClassifier, KerasRegressor
from sklearn.model_selection import StratifiedKFold, KFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from . import prep, io, train


def kfold_cross_val(df, target_col, bucket_mod, data_path, verbose, n_jobs, kfold):
    k = np.abs(kfold)
    # evaluate using 10-fold cross validation
    X, y = prep.split_Xy(df, target_col)
    # run estimator
    if target_col == "mem_bin":
        # Y = y.reshape(-1, 1)
        encoder = LabelEncoder()
        y = encoder.fit_transform(y)
        # y_enc = keras.utils.to_categorical(y)
        estimator = KerasClassifier(build_fn=train.memory_classifier, epochs=60, batch_size=32, verbose=verbose)
        kfold = StratifiedKFold(n_splits=k, shuffle=True)
    elif target_col == "memory":
        estimator = KerasRegressor(build_fn=train.memory_regressor, epochs=60, batch_size=32, verbose=verbose)
        kfold = KFold(n_splits=k, shuffle=True)
    elif target_col == "wallclock":
        estimator = KerasRegressor(build_fn=train.wallclock_regressor, epochs=300, batch_size=32, verbose=verbose)
        kfold = KFold(n_splits=k, shuffle=True)
    print("\nStarting KFOLD Cross-Validation...")
    start = time.time()
    results = cross_val_score(estimator, X, y, cv=kfold, n_jobs=n_jobs)
    end = time.time()
    duration = io.proc_time(start, end)
    if target_col == "mem_bin":
        score = np.mean(results)
    else:
        score = np.sqrt(np.abs(np.mean(results)))
    print(f"\nKFOLD scores: {results}\n")
    print(f"\nMean Score: {score}\n")
    print("\nProcess took ", duration)
    kfold_dict = {"kfold": {"results": list(results), "score": score, "time": duration}}
    keys = io.save_to_pickle(kfold_dict, target_col=target_col)
    io.s3_upload(keys, bucket_mod, f"{data_path}/results")


def run_kfold(df, bucket_mod, data_path, models, verbose, n_jobs, kfold):
    for target in models:
        kfold_cross_val(df, target, bucket_mod, data_path, verbose, n_jobs, kfold)
