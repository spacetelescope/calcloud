import csv
import time

import boto3
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


def get_dynamo_items(number_items):
    """Get data from dynamo"""
    session = boto3.Session(profile_name="aws-hst-repro-ops-Developer")
    dynamodb = session.resource("dynamodb")
    table = dynamodb.Table("calcloud-model-ops")
    items = []
    response = table.scan(Limit=number_items)
    items.extend(response["Items"])

    while "LastEvaluatedKey" in response and len(items) < number_items:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"], Limit=number_items)
        items.extend(response["Items"])

    items = items[:number_items]

    return items


input_keys = ("n_files", "total_mb", "drizcorr", "pctecorr", "crsplit", "subarray", "detector", "dtype", "instr")
prediction_keys = ("mem_pred", "wall_pred", "bin_pred", "wc_mean", "wc_err", "wc_std", "x_mean", "x_files")
actual_keys = ("memory", "wallclock", "mem_bin")


def convert_elements_to_numeric_values(items):
    """Clean up the data, converting strings to numeric values"""
    for item in items:
        item["inputs"] = {}
        item["predictions"] = {}
        item["actuals"] = {}
        for key in input_keys:
            value = item.pop(key)
            try:
                item["inputs"][key] = int(value)
            except ValueError:
                item["inputs"][key] = np.float64(value)
        for key in prediction_keys:
            value = item.pop(key, None)
            if value is not None and value != "":
                item["predictions"][key] = np.float64(value)
        for key in actual_keys:
            item["actuals"][key] = np.float64(item.pop(key))


def save_data_as_csv(items):
    """Save the items as a CSV for later re-processing"""
    flat_items = [x["inputs"] | x["predictions"] | x["actuals"] for x in items]
    with open("data.csv", "w") as f:
        headers = list(input_keys) + list(prediction_keys) + list(actual_keys)
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(flat_items)


def calculate_memory_model(data):
    """Calculate the model for memory, analyze result, present actual vs. predicted"""
    df = pd.DataFrame(data)
    original_df = pd.DataFrame(data)

    df = pd.get_dummies(
        original_df,
        columns=["instr", "dtype", "detector", "drizcorr", "pctecorr", "crsplit", "subarray"],
        drop_first=True,
    )

    X = df.drop(columns=["wallclock", "memory"])
    y = df["memory"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Memory model
    memory_model = HistGradientBoostingRegressor(max_depth=5, learning_rate=0.05, max_iter=500, random_state=42)
    memory_model.fit(X_train, y_train)
    actual_memory = y_test
    predicted_memory = memory_model.predict(X_test)

    memory_r2 = r2_score(y_test, predicted_memory)
    memory_mae = mean_absolute_error(y_test, predicted_memory)
    memory_rmse = np.sqrt(mean_squared_error(y_test, predicted_memory))
    memory_mape = np.mean(np.abs((y_test - predicted_memory) / y_test)) * 100

    print("\nMemory")
    print(f"  R²   = {memory_r2:.3f}")
    print(f"  MAE  = {memory_mae:.2f}")
    print(f"  RMSE = {memory_rmse:.2f}")
    print(f"  MAPE = {memory_mape:.1f}%")
    print("")

    joblib.dump({"model": memory_model, "columns": list(X.columns)}, "scripts/memory_model.pkl")

    plot_actual_vs_predicted(
        actual_memory,
        predicted_memory,
        xlabel="Actual Memory",
        ylabel="Predicted Memory",
        title="Memory Predicted vs Actual",
    )

    confirm_prediction(X_test, predicted_memory)


def confirm_prediction(X_test, in_predicted, for_wallclock=False):
    if for_wallclock:
        model_path = "scripts/wallclock_model.pkl"
    else:
        model_path = "scripts/memory_model.pkl"
    saved = joblib.load(model_path)
    model = saved["model"]
    feature_columns = saved["columns"]

    test_df = X_test.iloc[0]
    if for_wallclock:
        test_dict = {"n_files": np.expm1(test_df["log_n_files"]), "total_mb": np.expm1(test_df["log_total_mb"])}
    else:
        test_dict = {"n_files": test_df["n_files"], "total_mb": test_df["total_mb"]}
    test_dict |= {
        "dtype": int(test_df["dtype_1"]),
        "detector": int(test_df["detector_1"]),
        "drizcorr": int(test_df["drizcorr_1"]),
        "pctecorr": int(test_df["pctecorr_1"]),
        "subarray": int(test_df["subarray_1"]),
    }
    if test_df["instr_1"]:
        test_dict["instr"] = 1
    elif test_df["instr_2"]:
        test_dict["instr"] = 2
    elif test_df["instr_3"]:
        test_dict["instr"] = 3
    else:
        test_dict["instr"] = 0
    if test_df["crsplit_1"]:
        test_dict["crsplit"] = 1
    elif test_df["crsplit_2"]:
        test_dict["crsplit"] = 2
    else:
        test_dict["crsplit"] = 0

    feature_dict = test_dict
    feature_df = build_feature_frame(feature_dict, feature_columns, for_wallclock=for_wallclock)

    out_predicted = model.predict(feature_df)[0]
    if for_wallclock:
        out_predicted = float(np.expm1(out_predicted))
    if out_predicted == in_predicted[0]:
        print(f"SUCCESS: Predicted match (wallclock={for_wallclock}): in={in_predicted[0]} vs out={out_predicted}")
    else:
        print(f"ERROR: Predicted mismatch (wallclock={for_wallclock}): in={in_predicted[0]} vs out={out_predicted}")


def build_feature_frame(feature_dict, feature_columns, for_wallclock=False):
    """Recreate training-time preprocessing for one-row prediction."""
    categorical_cols = ["instr", "dtype", "detector", "drizcorr", "pctecorr", "crsplit", "subarray"]

    df = pd.DataFrame([feature_dict]).copy()

    if for_wallclock:
        df["log_n_files"] = np.log1p(df["n_files"])
        df["log_total_mb"] = np.log1p(df["total_mb"])
    else:
        df["n_files"] = df["n_files"].astype(float)
        df["total_mb"] = df["total_mb"].astype(float)

    for col in categorical_cols:
        df[col] = feature_dict[col]

    df = pd.get_dummies(df, columns=categorical_cols, drop_first=False)

    # Match the exact training feature order and fill unseen categories with 0.
    feature_df = df.reindex(columns=feature_columns, fill_value=0.0)
    return feature_df.astype(float)


def predict_memory(feature_dict):
    """Predict memory in GB and memory bin for a given feature dict."""
    model_path = "lambda/JobPredict/models/memory_model.pkl"
    saved = joblib.load(model_path)
    memory_model = saved["model"]
    feature_columns = saved["columns"]

    feature_df = build_feature_frame(feature_dict, feature_columns, for_wallclock=False)

    predicted_memory = memory_model.predict(feature_df)[0]

    memory = predicted_memory * 1.10
    if memory < 2:
        predicted_bin = 0
    elif memory < 8:
        predicted_bin = 1
    elif memory < 16:
        predicted_bin = 2
    else:
        predicted_bin = 3
    return predicted_memory, predicted_bin


def predict_wallclock(feature_dict):
    """Predict wallclock time in seconds for a given feature dict."""
    model_path = "lambda/JobPredict/models/wallclock_model.pkl"
    saved = joblib.load(model_path)
    wallclock_model = saved["model"]
    feature_columns = saved["columns"]

    feature_df = build_feature_frame(feature_dict, feature_columns, for_wallclock=True)

    log_prediction = float(wallclock_model.predict(feature_df)[0])
    prediction = float(np.expm1(log_prediction))
    return prediction


def plot_actual_vs_predicted(actual, predicted, xlabel, ylabel, title, use_log_log_scale=False, save=False):
    """Plot actual vs. predicted"""
    plt.figure(figsize=(8, 8))

    plt.scatter(actual, predicted, alpha=0.6, edgecolors="none")

    if use_log_log_scale:
        plt.xscale("log")
        plt.yscale("log")

    # Perfect prediction line
    min_val = min(actual.min(), predicted.min())
    max_val = max(actual.max(), predicted.max())

    plt.plot([min_val, max_val], [min_val, max_val], "r--", linewidth=2, label="Perfect prediction")

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    if save:
        plt.savefig(f"{title}.png")
    else:
        plt.show()
    plt.close()


def calculate_wallclock_model(data):
    """Calculate the model for wallclock, analyze result, present actual vs. predicted"""
    df = pd.DataFrame(data)
    original_df = pd.DataFrame(data)

    df = pd.get_dummies(
        original_df,
        columns=["instr", "dtype", "detector", "drizcorr", "pctecorr", "crsplit", "subarray"],
        drop_first=True,
    )
    df["log_total_mb"] = np.log1p(df["total_mb"])
    df["log_n_files"] = np.log1p(df["n_files"])

    X = df.drop(columns=["wallclock", "memory", "total_mb", "n_files"])
    y = np.log1p(df["wallclock"])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Wallclock model
    wallclock_model = HistGradientBoostingRegressor(max_depth=5, learning_rate=0.05, max_iter=500, random_state=42)
    wallclock_model.fit(X_train, y_train)

    log_pred = wallclock_model.predict(X_test)

    predicted_wallclock = np.expm1(log_pred)
    actual_wallclock = np.expm1(y_test)

    log_r2 = r2_score(y_test, log_pred)

    mae = mean_absolute_error(y_test, log_pred)
    rmse = np.sqrt(mean_squared_error(y_test, log_pred))

    ape = (np.abs(predicted_wallclock - actual_wallclock) / actual_wallclock) * 100
    mean_ape = np.mean(ape)
    median_ape = np.median(ape)
    ape_95 = np.percentile(ape, 95)
    ape_99 = np.percentile(ape, 99)

    print("\nWallclock")
    print(f"  Log-space R²   = {log_r2:.3f}")
    print(f"  Log-space MAE  = {mae:.2f}")
    print(f"  Log-space RMSE = {rmse:.2f}")
    print(f"  Mean APE       = {mean_ape:.1f}%")

    print(f"  Median APE     = {median_ape:.1f}%")
    print(f"  95th pct APE   = {ape_95:.1f}%")
    print(f"  99th pct APE   = {ape_99:.1f}%")

    joblib.dump({"model": wallclock_model, "columns": list(X.columns)}, "scripts/wallclock_model.pkl")

    plot_actual_vs_predicted(
        actual_wallclock,
        predicted_wallclock,
        xlabel="Actual Wallclock",
        ylabel="Predicted Wallclock",
        title="Wallclock: Predicted vs Actual (Log Scale)",
        use_log_log_scale=True,
    )

    confirm_prediction(X_test, predicted_wallclock, for_wallclock=True)


def calculate_models(items):
    """Create and evaluate the models"""
    data = {}
    for input_key in input_keys:
        data[input_key] = [x["inputs"][input_key] for x in items]
    for output_key in ("wallclock", "memory"):
        data[output_key] = [x["actuals"][output_key] for x in items]
    calculate_memory_model(data)
    calculate_wallclock_model(data)


def plot_bins(items):
    """Plot memory and wallclock in bins to see distribution"""
    fig, axs = plt.subplots(1, 2, figsize=(18, 6), layout="constrained")

    deciles_array = np.arange(10, 100, 10)

    # Plot wallclock
    percent = 100
    cutoff = 0
    wallclock = [x["actuals"]["wallclock"] for x in items]
    wallclock = [x for x in wallclock if x > cutoff]
    deciles = np.percentile(wallclock, deciles_array)

    label = f"{len(wallclock)} samples\n"
    if cutoff != 0:
        label += f"(wallclock > {cutoff} s)\n"
    label += f"D10: {deciles[0]:.2f}\n" f"D50 (Med): {deciles[4]:.2f}\n" f"D90: {deciles[8]:.2f}"
    axs[0].hist(wallclock, bins="auto", edgecolor="black", color="skyblue")
    title = "Wallclock Distribution"
    if percent != 100:
        title += f" (top {percent}%)"
    axs[0].set_title(title)
    axs[0].set_xlabel("Wallclock (s)")
    axs[0].set_ylabel("Frequency")
    axs[0].text(0.60, 0.95, label, transform=axs[0].transAxes, horizontalalignment="left", verticalalignment="top")

    # Plot memory
    cutoff = 0
    memory = [x["actuals"]["memory"] for x in items]
    memory = [x for x in memory if x > cutoff]
    deciles = np.percentile(memory, deciles_array)

    label = f"{len(memory)} samples\n"
    if cutoff != 0:
        label += f"(memory > {cutoff} GB)\n"
    label += f"D10: {deciles[0]:.2f}\n" f"D50 (Med): {deciles[4]:.2f}\n" f"D90: {deciles[8]:.2f}"
    axs[1].hist(memory, bins="auto", edgecolor="black", color="salmon")
    title = "Memory Distribution"
    if percent != 100:
        title += f" (top {percent}%)"
    axs[1].set_title(title)
    axs[1].set_xlabel("Memory (GB)")
    axs[1].text(0.60, 0.95, label, transform=axs[1].transAxes, horizontalalignment="left", verticalalignment="top")

    # 5. Clean up layout spacing and display
    plt.tight_layout()
    plt.show()


def evaluate_model_prediction(items):
    from JobPredict import predict_handler

    # load models
    clf = predict_handler.get_model("lambda/JobPredict/models/mem_clf/")
    mem_reg = predict_handler.get_model("lambda/JobPredict/models/mem_reg/")
    wall_reg = predict_handler.get_model("lambda/JobPredict/models/wall_reg/")
    pt_data = predict_handler.load_pt_data("lambda/JobPredict/models/pt_transform")

    start_time = time.time()
    for item in items:
        prep = predict_handler.Preprocess(None, None, None)
        inputs = item["inputs"]
        prep.inputs = np.array(
            [
                inputs["n_files"],
                inputs["total_mb"],
                inputs["drizcorr"],
                inputs["pctecorr"],
                inputs["crsplit"],
                inputs["subarray"],
                inputs["detector"],
                inputs["dtype"],
                inputs["instr"],
            ]
        )
        X = prep.transformer(pt_data)

        # Predict Memory Allocation (bin and value preds)
        membin, pred_proba = predict_handler.classifier(clf, X)
        memval = np.round(float(predict_handler.regressor(mem_reg, X)), 2)
        # Predict Wallclock Allocation (execution time in seconds)
        clocktime = int(predict_handler.regressor(wall_reg, X))
        item["model_predictions"] = {"mem_bin": membin, "mem_val": memval, "clocktime": clocktime}
        if time.time() - start_time > 3600:
            break

    f = open("output", "w")
    items = [x for x in items if "model_predictions" in x]
    f.write(f"{len(items)} items\n")

    df = pd.DataFrame([x["actuals"] | x["model_predictions"] for x in items])
    actual_memory = df["memory"]
    predicted_memory = df["mem_val"]

    memory_r2 = r2_score(actual_memory, predicted_memory)
    memory_mae = mean_absolute_error(actual_memory, predicted_memory)
    memory_rmse = np.sqrt(mean_squared_error(actual_memory, predicted_memory))
    memory_mape = np.mean(np.abs((actual_memory - predicted_memory) / actual_memory)) * 100

    f.write("\nMemory\n")
    f.write(f"  R²   = {memory_r2:.3f}\n")
    f.write(f"  MAE  = {memory_mae:.2f}\n")
    f.write(f"  RMSE = {memory_rmse:.2f}\n")
    f.write(f"  MAPE = {memory_mape:.1f}%\n")
    f.write("\n")

    plot_actual_vs_predicted(
        actual_memory,
        predicted_memory,
        "Actual Memory",
        "Memory Predicted by Model",
        "Predicted vs. Actual Memory",
        use_log_log_scale=False,
        save=True,
    )

    actual_wallclock = df["wallclock"]
    predicted_wallclock = df["clocktime"]

    log_actual_wallclock = np.log1p(actual_wallclock)
    log_predicted_wallclock = np.log1p(predicted_wallclock)

    log_r2 = r2_score(log_actual_wallclock, log_predicted_wallclock)

    mae = mean_absolute_error(log_actual_wallclock, log_predicted_wallclock)
    rmse = np.sqrt(mean_squared_error(log_predicted_wallclock, log_predicted_wallclock))

    ape = (np.abs(predicted_wallclock - actual_wallclock) / actual_wallclock) * 100
    mean_ape = np.mean(ape)
    median_ape = np.median(ape)
    ape_95 = np.percentile(ape, 95)
    ape_99 = np.percentile(ape, 99)

    f.write("\nWallclock\n")
    f.write(f"  Log-space R²   = {log_r2:.3f}\n")
    f.write(f"  Log-space MAE  = {mae:.2f}\n")
    f.write(f"  Log-space RMSE = {rmse:.2f}\n")
    f.write(f"  Mean APE       = {mean_ape:.1f}%\n")

    f.write(f"  Median APE     = {median_ape:.1f}%\n")
    f.write(f"  95th pct APE   = {ape_95:.1f}%\n")
    f.write(f"  99th pct APE   = {ape_99:.1f}%\n")

    plot_actual_vs_predicted(
        actual_wallclock,
        predicted_wallclock,
        "Actual Wallclock",
        "Wallclock Predicted by Model",
        "Predicted vs. Actual Wallclock (Log-Log Scale)",
        use_log_log_scale=True,
        save=True,
    )


def test_remotely():
    with open("data.csv") as f:
        reader = csv.DictReader(f)
        items = list(reader)
    convert_elements_to_numeric_values(items)

    evaluate_model_prediction(items)


def test_locally():
    items = get_dynamo_items(1000000)  
    convert_elements_to_numeric_values(items)
    # save_data_as_csv(items)

    plot_bins(items)
    calculate_models(items)

    row = {
        "n_files": 2,
        "total_mb": np.float64(9.0),
        "drizcorr": 0,
        "pctecorr": 0,
        "crsplit": 0,
        "subarray": 1,
        "detector": 0,
        "dtype": 0,
        "instr": 1,
    }

    # row from test_lambda_job_predict.py
    row = {
        "n_files": 1,
        "total_mb": 10,
        "drizcorr": 0,
        "pctecorr": 1,
        "crsplit": 1,
        "subarray": 0,
        "detector": 1,
        "dtype": 1,
        "instr": 3,
    }
    predicted_memory, predicted_bin = predict_memory(row)
    predicted_wallclock = predict_wallclock(row)
    a = 1


def main():
    test_locally()


if __name__ == "__main__":
    main()
