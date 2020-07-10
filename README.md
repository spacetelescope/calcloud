CalCloud Repo!

This project contains software which orchestrates running large numbers of
STScI (Space Telescope Science Institute) calibration containers on some form
of AWS cluster.  The system supported could be dubbed a "macro-pipeline" which
is used to run arbitrary numbers of "micro-pipeline" jobs.

Its scope is roughly:

1. Handling a web request initiating the higher level processing of a batch of
telescope datasets.

2. Defining and managing the cluster resources associated with running jobs.

3. Managing any messaging associated with running jobs and copying results.

4. Copying results from each dataset from S3 to some other host.

Initially the container supported will be defined by the caldp package which
supports calibrating data from the Hubble Space Telescope (HST).  caldp defines
a "nano-pipeline" capable of fully processing a single dataset, including
obtaining the data, assigning and obtaining reference files, running HST
calibration programs (e.g. calacs.e), creating preview files of the output
data, and copying all outputs, previews, logs, and metrics to AWS S3 storage.
