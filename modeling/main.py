import sys
import os
import shutil
from . import io
from . import prep
from . import train
from . import validate


def get_training_config(args):
    valid_opts = ["build", "update"]
    valid_mods = ["all", "mem_bin", "memory", "wallclock"]
    if len(args) > 2:
        opt, mod = args[1], args[2:]
    elif len(args) == 2:
        opt, mod = args[1], ["all"]
    else:  # use defaults
        opt, mod = "build", ["all"]
    # validate training option
    if opt not in valid_opts:
        print(f"Invalid option arg: {opt}")
        print(f"Options: {valid_opts}")
        opt = "build"
    # validate model arg
    if "all" in mod:
        models = ["mem_bin", "memory", "wallclock"]
    else:
        models = mod
    for m in models:
        if m not in valid_mods:
            print(f"Invalid model arg: {m}")
            print(f"Mods: {valid_mods}\n")
            sys.exit(1)
        else:
            continue
    print(f"{opt} models: {models}")
    return opt, models


if __name__ == "__main__":
    # python -m modeling.main [build, update] [all, mem_bin, memory, wallclock]
    # default args: [build] [all] # builds and trains all models using all data
    args = sys.argv
    opt, models = get_training_config(args)
    # set default Env vars
    bucket_mod = os.environ.get("S3MOD", "calcloud-modeling-sb")  # where to pull and store metadata
    timestamp = os.environ.get("TIMESTAMP", "now")  # results saved to timestamped directory (s3)
    verbose = os.environ.get("VERBOSE", 0)  # print everything to stdout (set=1 for debug)
    cross_val = os.environ.get("KFOLD", None)  # 'only', 'skip', None or "None"
    src = os.environ.get("DATASOURCE", "ddb")  # s3:latest
    table_name = os.environ.get("DDBTABLE", "calcloud-model-sb")
    attr_name = os.environ.get("ATTRNAME", "None")
    attr_method = os.environ.get("ATTRMETHOD", "None")
    attr_type = os.environ.get("ATTRTYPE", "None")
    attr_val = os.environ.get("ATTRVALUE", "None")
    n_jobs = int(os.environ.get("NJOBS", -2))

    # get subset from dynamodb
    if attr_name != "None":
        attr = {"name": attr_name, "method": attr_method, "value": attr_val, "type": attr_type}
    else:
        attr = None
    # load training data
    prefix = io.get_paths(timestamp)
    home = os.path.join(os.getcwd(), prefix)
    os.makedirs(f"{prefix}/data", exist_ok=True)
    os.chdir(f"{prefix}/data")
    df = prep.preprocess(bucket_mod, prefix, src, table_name, attr)
    os.chdir(home)
    if cross_val == "only":
        # run_kfold, skip training
        validate.run_kfold(df, bucket_mod, prefix, models, verbose, n_jobs)
    else:
        df_new = train.train_models(df, bucket_mod, prefix, opt, models, verbose)
        io.save_dataframe(df_new, "latest.csv")
        io.s3_upload(["latest.csv"], bucket_mod, f"{prefix}/data")
        shutil.copy(f"data/pt_transform", "./models/pt_transform")
        io.zip_models("./models", zipname="models.zip")
        io.s3_upload(["models.zip"], bucket_mod, f"{prefix}/models")
        io.batch_ddb_writer("latest.csv", table_name)

        if cross_val == "skip":
            print("Skipping KFOLD")
        else:
            validate.run_kfold(df, bucket_mod, prefix, models, verbose, n_jobs)
