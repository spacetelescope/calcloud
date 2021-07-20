import sys, os
from . import io, prep, train, validate

def get_training_config(args):
    valid_opts = ["build", "update"]
    valid_mods = ["all", "mem_bin", "memory", "wallclock"]
    if len(args) > 2:
        opt, mod = args[1], args[2:]
    elif len(args) == 2:
        opt, mod = args[1], ["all"]
    else: # use defaults
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
    bucket_mod = os.environ.get("S3MOD", "calcloud-modeling-sb") # where to pull and store metadata
    timestamp = os.environ.get("TIMESTAMP", "now")  # results saved to timestamped directory (s3)
    verbose = os.environ.get("VERBOSE", 0) # print everything to stdout (set=1 for debug)
    cross_val = os.environ.get("KFOLD", None) # 'only', 'skip', None or "None"
    src = os.environ.get("DATASOURCE", "ddb") # s3:latest
    table_name = os.environ.get("DDBTABLE", "calcloud-model-sb")
    attr_name = os.environ.get("ATTRNAME", "None")
    attr_method = os.environ.get("ATTRMETHOD", "None")
    attr_val = os.environ.get("ATTRVAL", "None")
    attr_type = os.environ.get("ATTRTYPE", "None")
    if attr_name != "None":
        # get subset from dynamodb
        attr = {"name": attr_name, "method": attr_method, "value": attr_val}
    else:
        attr = None
    # load training date
    data_path = io.get_paths(timestamp)
    home = os.path.join(os.getcwd(), data_path)
    prefix = f"{data_path}/data"
    os.makedirs(prefix, exist_ok=True)
    os.chdir(prefix)
    df = prep.preprocess(bucket_mod, prefix, src, table_name, attr)
    os.chdir(home)
    if cross_val == "only":
        # run_kfold, skip training
        validate.run_kfold(df, bucket_mod, data_path, models, verbose)
    else:
        train.train_models(df, bucket_mod, data_path, opt, models, verbose)
        io.zip_models("./models", zipname="models.zip")
        io.s3_upload(["models.zip"], bucket_mod, f"{data_path}/models")
        if cross_val == "skip":
            print("Skipping KFOLD")
        else:
            validate.run_kfold(df, bucket_mod, data_path, models, verbose)
