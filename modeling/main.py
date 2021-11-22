import os
import shutil
import argparse
from . import io
from . import prep
from . import train
from . import validate


def set_training_config(args):
    models = []
    mods = [args.m1, args.m2, args.m3]
    models = [m for m in mods if m is not None]
    if args.update is True:
        opt = "update"
    else:
        opt = "build"
    print(f"{opt} models: {models}")
    # optionally get subset from dynamodb
    if args.attrname != "None":
        attr = {"name": args.attrname, "method": args.attrmethod, "value": args.attrval, "type": args.attrtype}
    else:
        attr = None
    return opt, models, attr


if __name__ == "__main__":
    # default: builds and trains all models using all data from dynamodb table
    parser = argparse.ArgumentParser(
        prog="calcloud", description="resource prediction model training", usage="python -m modeling.main"
    )
    parser.add_argument("--m1", default="mem_bin", help="train memory bin classifier")
    parser.add_argument("--m2", default="memory", help="train memory regressor")
    parser.add_argument("--m3", default="wallclock", help="train wallclock regressor")
    parser.add_argument("-u", "--update", default=False, help="fetch-update latest models (vs build from scratch)")
    parser.add_argument(
        "-k",
        "--kfold",
        choices=[-10, -5, 0, 5, 10],
        default=0,
        help="n kfolds for cross-validation. 0: skip; -10,-5: kfold only; 5,10: kfold post training",
    )
    parser.add_argument("-j", "--njobs", type=int, default=-2, help="proc thread usage for kfold jobs")
    parser.add_argument("-n", "--attrname", type=str, default="None")
    parser.add_argument("-m", "--attrmethod", type=str, default="None")
    parser.add_argument("-t", "--attrtype", type=str, default="None")
    parser.add_argument("-v", "--attrvalue", default="None")
    # get/set default Env vars
    bucket_mod = os.environ.get("S3MOD", "calcloud-modeling-sb")  # where to pull and store metadata
    timestamp = os.environ.get("TIMESTAMP", "now")  # results saved to timestamped directory (s3)
    verbose = os.environ.get("VERBOSE", 0)  # print everything to stdout (set=1 for debug)
    src = os.environ.get("DATASOURCE", "ddb")  # "ddb" (default) or "s3:prefix" (will be deprecated)
    table_name = os.environ.get("DDBTABLE", "calcloud-model-sb")
    # get user args
    args = parser.parse_args()
    opt, models, attr = set_training_config(args)
    kfold, n_jobs = args.kfold, args.n_jobs
    # load training data
    prefix = io.get_paths(timestamp)
    home = os.path.join(os.getcwd(), prefix)
    os.makedirs(f"{prefix}/data", exist_ok=True)
    os.chdir(f"{prefix}/data")
    df = prep.preprocess(bucket_mod, prefix, src, table_name, attr)
    os.chdir(home)
    if kfold < 0:  # -10,-5: only run kfold, no training
        validate.run_kfold(df, bucket_mod, prefix, models, verbose, n_jobs, kfold)
    else:  # 0: skip; 5,10: post training
        df_new = train.train_models(df, bucket_mod, prefix, opt, models, verbose)
        io.save_dataframe(df_new, "latest.csv")
        io.s3_upload(["latest.csv"], bucket_mod, f"{prefix}/data")
        shutil.copy("data/pt_transform", "./models/pt_transform")
        io.zip_models("./models", zipname="models.zip")
        io.s3_upload(["models.zip"], bucket_mod, f"{prefix}/models")
        io.batch_ddb_writer("latest.csv", table_name)
        if kfold > 0:
            validate.run_kfold(df, bucket_mod, prefix, models, verbose, n_jobs, kfold)
        else:
            print("Skipping KFOLD")
