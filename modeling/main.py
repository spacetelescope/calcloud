import os
from . import io, ingest, train

if __name__ == "__main__":
    bucket_mod = os.environ.get("S3MOD", "calcloud-modeling-sb")
    bucket_proc = os.environ.get("S3PROC", "calcloud-processing-sb")
    log_group = os.environ.get("LOGPRED", "/aws/lambda/calcloud-job-predict-sb")
    scrapetime = os.environ.get("SCRAPETIME", "now")  # final log event time
    hr_delta = int(os.environ.get("HRDELTA", 1))  # how far back in time to start
    mins = int(os.environ.get("MINS", 10))  # num minutes forward to scrape
    verbose = os.environ.get("VERBOSE", 0)
    print("URIs: ", bucket_mod, bucket_proc, log_group)
    print("OPTIONS: ", scrapetime, hr_delta, mins)
    t0, data_path = io.get_paths(scrapetime, hr_delta)
    home = os.path.join(os.getcwd(), data_path)
    prefix = f"{data_path}/data"
    os.makedirs(prefix, exist_ok=True)
    os.chdir(prefix)
    F, T, P = ingest.scrape_all(bucket_mod, bucket_proc, prefix, log_group, t0, mins)
    df = train.preprocess(F, T, P, bucket_mod, prefix, download=False)
    print("Scraped data saved in ", data_path)
    os.chdir(home)
    train.train_models(df, bucket_mod, data_path, opt="build", mod="all", verbose=verbose)
    io.zip_models("./models", zipname="models.zip")
    io.s3_upload(["models.zip"], bucket_mod, f"{data_path}/models")
