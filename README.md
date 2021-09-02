CalCloud Repo!
==============

Calcloud orchestrates running large numbers of STScI (Space Telescope Science
Institute) calibration containers on AWS Batch.  CalCloud could be dubbed a
"macro-pipeline" which is used to run arbitrary numbers of CALDP
"micro-pipeline" jobs.

CALDP
=====

The [CALDP](https://github.com/spacetelescope/caldp.git) Docker image is
managed as a seperate project and used to process one HST IPPPSSOOT.  Multiple
steps are performed in series in a single container run.  Steps include
fetching data from AWS S3 storage, assigning and obtaining reference files,
running HST calibration programs (e.g. calacs.e), drizzling, creating preview
files of the output data, and copying all outputs, previews, logs, and metrics
to AWS S3 storage.

CalCloud
========

[CalCloud](https://github.com/spacetelescope/calcloud.git) runs thousands of
CALDP jobs in parallel by:

1. Provisioning and managing the required AWS Batch and other resources
associated with running jobs.

2. Processing each set of inputs (one IPPPSSOOT) as an AWS Batch job running a
CALDP container.  Inputs are prepared by and uploaded from on premise systems
to AWS S3.

3. Recieving and sending messages associated with job submission, completion,
failure, rescue, and cleanup.   These messages are triggered by S3 file i/o
and handled by lambdas.

4. Downloading results for each IPPPSSOOT from S3 to on premise systems
for archiving.

5. Predicting job memory and runtime requirements, and assigning each job to
the most efficient AWS EC2 instance capable of processing it.  Continually
retraining the prediction model using actual/observed memory and runtime from
completed jobs.

6. Delivering key CalCloud / AWS Batch status via a blackboard file to the on
premise OWL GUI where it is displayed for operators.

Development cycle and CI
==========================

Gitflow
-------

This repository is organized under the [Gitflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)
model. Feature branches can be PR'ed into `develop` from forks. To the extent that 
is reasonable, developers should follow these tenets of the Gitflow model:

- feature branches should be started off of `develop`, and PR'ed back into `develop`
- release candidates should branch off of `develop`, be PR'ed into `main`, and
  merged back into `develop` during final release.
- hotfixes should branch off of `main`, be PR'ed back to `main`, and be merged back 
  to `develop` after release.

While developers are free to work on features in their forks, it is preferred for releases
and hotfixes to be prepared via branches on the primary repository.

Our github action workflow `merge-main-to-develop` runs after any push to `main`, 
(which automatically includes merged PR's). In practice this is a slight deviation 
from Gitflow, which would merge the release or hotfix branch into `develop`. However, 
due to the nature of github action permissions, the github action triggered by a PR from 
a fork does not have sufficient scope to perform that secondary merge directly from the 
PR commit. This security limitation would require a personal access token of an admin to 
be added to the account to allow github actions to merge. By merging from `main` right 
after push, the github action has sufficient privilege to push to `develop`. The 
implication being that the security of code added via PR from a fork falls on the 
administrators of this project, and is not inadvertently circumvented via github action 
elevated privileges.

Github Actions
--------------
The calcloud repo is set up for GitHub Actions with the following workflows:

- code checks:  flake8, black, and bandit checks

Whenever you do a PR or merge to spacetelescope/calcloud, GitHub will
automatically run CI tests for calcloud.

Additionally, there are several workflows that aid in managing the 
[Gitflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)
workflow.

- tag-latest: automatically tags the latest commit to `develop` as `latest`
- tag-stable: automatically tags the latest commit to `main` as `stable`
- merge-main-to-develop: merges `main` back down to `develop` after any push to `main`
- check-merge-main2develop: checks for merge failures with `develop`, for any PR to `main`. 
  For information only; indicates that manual merge conflict resolution may be required 
  to merge this PR back into `develop`. Not intended to block PR resolution, and no attempt 
  to resolve the conflict is needed prior to merging `main`.


Architecture
============

Processing
----------

CalCloud is used to run HST reprocessing jobs on the AWS Batch service using
semi-arbitrary numbers of EC2 instances to accelerate processing rates.  On
premise systems prepare reprocessing job inputs using HT Condor jobs, write
them to the File Gateway, and trigger AWS Batch jobs by writing `submit`
messages.  These inputs and messages are mirrored to AWS S3 by the File Gateway
where they trigger lambdas to enqueue AWS Batch jobs.  When the CALDP Batch job
is finally scheduled and completes, its outputs and a `processed.trigger`
message are written back to S3 where they are mirrored by the File Gateway back
to the on premise NFS mount.  On premise pollers eventually spot the
`processed.trigger` message and initiate HT Condor jobs to archive the
processed data.

Job Ladder
----------

Each HST job has different requirements for memory and runtime and different
opportunities to utilize multiple cores.  The consequences of a job exhausting
all available memory is often instant termination.  Consequently, considerable
effort is spent on predicting job requirements and scheduling jobs on EC2
types capable of processing them to completion.

CalCloud uses a "job ladder" where each rung corresponds to a different AWS
Batch queue which is in turn associated with a particular EC2 instance type.
There are 2G, 8G, 16G, and 64G memory rungs on the ladder and any job assigned
to that rung is given that amount of memory to use.

A neural network has been developed to predict which rung to use as a starting
point for any particular IPPPSSOOT.  If a job fails due to memory exhaustion,
it is automatically rescued and re-submitted on the next highest rung where it
will have additional memory with which to succeed.  If a job fails running on
the 64G rung due to memory exhaustion, it is not automatically rescued.

AWS Batch Resource Organization
-------------------------------

The job ladder has a relatively simple mapping onto AWS batch resources
representing each rung of the ladder.  Each 2G, 8G, 16G, or 64G ladder rung
has:

1. a queue

2. a compute environment defining a limited set of instance types tuned to
the memory requirements of the rung.  the 2G rung may eventually use fargate
rather than EC2 instances.

3. a job definition defining the available resources for each job run on
that rung.

While AWS Batch can support much more complex relationships,  the CalCloud
configuration is 1:1:1,  4 linear rungs.

Many other aspects of all jobs are constant, e.g. the same command line
template, the same S3 bucket, and the same CALDP image are used for every rung
of the ladder.

Storage Gateway
---------------

Bidirectional communication between on premise systems and cloud systems is
performed using an AWS File Storage Gateway.  The gateway conveys input data,
output data, control, and blackbord information with comparatively high
throughput.  Onsite, the gateway appears as an NFS mounted file system which is
transparently mirrored to an S3 bucket on AWS.  Conversely, files written to S3
on AWS are transparently mirrored back to on premises NFS.  The synchronization
is not instant and generally imposes a lag between when a file is written to
NFS and seen in S3, and vice versa.

The S3 bucket and NFS directories are partitioned into 4 functionally oriented
subdirectories:

- data:  is organized by IPPPSSOOT and stores job inputs and outputs

- messages: are organized by message type.  messages are sent to request job
            submission, job cancellation, job rescue, and job cleanup.
            messages can also signal job state such as errored or ready for
            archiving.

- control: is organized by IPPPSSOOT and stores job error/retry information as
           well as inputs for the job requirements neural network evaluation.

- blackboard: stores information which is used on premises by the OWL GUI to
           display job and processing information.

A periodic lambda is used to force improve synchronization of the Storage
Gateway between AWS and on premise NFS by flushing the cache.  Flush rates
depend on the subdirectory being flushed.

Message Passing
---------------

Messages are sent by writing files to the messages directory of the S3 bucket.
This write can happen directly using S3 API calls,  or indirectly by writing
the message to the appropriate on premises NFS directory.  Likewise messages
can be viewed on either side of the Storage Gateway.

Often a Lambda is triggered when a message file of the corresponding type is
written,  e.g. "cancel-ipppssoot" triggers the JobDelete lambda.

There are a number of different message types where the broad meaning of the
message and IPPPSSOOT(s) it applies to is encoded in the name.  All messages
are of the form:

    <verb_or_state> - <noun_or_wildcard>

Some messages which communicate between on premise and AWS systems both
record state and request action:

- placed-ipppssoot : new job inputs are in position,  enqueue and/or begin processing

- processed.trigger-ipppssoot : tell on prem systems that ipppssoot has been processed
                                and outputs are ready for archiving.

Other messages are used to request action:

- cancel-ipppssoot : kill the job associated with that ipppssoot.

- rescue-ipppssoot : re-submit this job while tracking retries.  if it
                     previously failed due to memory, use a higher memory rung.

- clean-ipppssoot : delete all inputs, control, outputs, and messages for ipppssoot

- clean-ingested :  clean all ipppssoots in state ingested-ipppssoot, i.e. fully completed

- cancel-all, rescue-all, clean-all : shorthand for performing cancel, rescue,
                          or clean on every ipppssoot which currently has any
                          associated message.

- broadcast-uuid : use divide and conquer to rapidly output the messages defined in the
                    file body by writing smaller message sublists from many lambdas.

Other messages are used to record state:

- error-ipppssoot : this dataset failed every possible retry and is stopped.

- terminated-ipppssoot :  an operator requested this job be killed and it was.

- ingested-ipppssoot : the processed data for ipppssoot has been archived on premises.

- ingesterror-ipppssoot : the on premise archive ingest failed

Generally the body of the message file is irrelevant; the broadcast and error
messages are exceptions.

Error Handling
--------------

A variety of different container failure modes are handled by CALDP and
CalCloud using a Batch job completion lambda.  Based on different exit codes
and or text strings describing the failure, the completion lambda may
handle it by:

1. Retry the job with some max number of retries on the same instance.
2. Retry the job on any higher job memory ladder rungs.
3. Mark the job as failed and leave it stopped.
4. Doing nothing,  it's a successful job.

Batch job exit status is communicated by CALDP using a single byte code. In
particular, CALDP cannot directly communicate more descriptive text
explanations making it sometimes necessary to review the job log. Job exit
status can originate from 3 broad locations:

1. Individual job steps and sub-programs have independent exit codes which may
overlap each other.  These communicate program-specific failure modes.

2. CALDP maps failures occurring within particular blocks of orchestration code
to it's own exit code value space.  This disambiguates the codes from
individual steps and sub-programs and blurs somewhat the cause of failure in
exchange for knowing which step failed.

3. AWS Batch also utilizes the exit code to communicate different statuses when
CALDP error processing is skipped due to a failure in Docker, AWS Batch itself,
or job cancellation.  These codes can potentially overlap with (2) causing
ambiguity, but such overlaps are not currently known to exist and AWS Batch
also reports additional descriptive text which CALDP cannot helping to
disambiguate.

Memory Errors
.............

Memory errors are distinguished by the need to advance along a finite job ladder:

1. Container memory failure

2. Python memory error (reported)

3. Python memory error (unreported)

While they are reported to or by AWS Batch in this complex way, they are all
handled identically.

Other Errors
............

These are distinguished as either "retryable" or "not retryable".

1. CannotInspectContainer  - this can result when AWS Batch does not inspect an
                             exited/stopped container before it is deleted automatically,
                             and is a transient error related to EBS throughput and IOPS provisioning.

2. DockerTimeoutError       - Not clear what caused this,  AWS Batch error msg was:
                              *DockerTimeoutError: Could not transition to created; timed out after waiting 4m0s*

3. Job Cancelled           - An operator cancelled the job so it should not be retried.

4. Other errors            - No automatic rescue


Blackboard
==========
The data processing operations team at STSci maintains a database of metadata for every processing job of every dataset. In order to communicate that information from AWS to the on-premise system, a lambda function is run on a schedule (triggered by a cloudwatch event) to scrape the AWS Batch console with boto3 API calls. An ascii table is then uploaded to S3, which is copied on-premise by the storage gateway. A poller on-premise ingests the file into the database. 

This metadata is used in GUI applications for science operations staff to monitor job status. In AWS Batch, jobs are only guaranteed to persist in the AWS Batch console for 24 hours. If 20k jobs run over the weekend, monitoring that many jobs can become difficult without persisting this information. It also provides staff with an historical record of the number of jobs that are run in a typical timeframe, and the amount of CPU hours required. 

In our current implementation, the blackboard lambda runs on a 7 minute schedule. 7 minutes was chosen so as not to overlap with the storage gateway cache refresh operations, which are scheduled for submission every 5 minutes; we have observed the blackboard ascii file becoming corrupted in the on-premise NFS mount when the schedules line up at 5 minutes. The on-premise poller again runs on a schedule of a ~few minutes, so ultimately the on-premise database can be up to ~15 minutes behind the true AWS Batch Job status.

To speed up this sync, we could capture Batch state change events in CloudWatch and send them to lambda for ingestion into a dynamodb, which could then be either hooked up directly to the GUIs, or replicated in a more efficient fashion to the on-prem databases. 


Job Memory Models
================

Overview
--------

Pre-trained artificial neural networks are implemented in the pipeline to predict job resource requirements for HST. All three network architectures are built using the Keras functional API from the Tensorflow library. 

1. Memory Classifier
1D Convolutional Neural Network performs multi-class classification on 8 features to predict which of 4 possible "memory bins" is the most appropriate for a given dataset. An estimated probability score is assigned to each of the four possible target classes, i.e. Memory Bins, represented by an integer from 0 to 3. The memory size thresholds are categorized as follow:

  - `0: < 2GB`
  - `1: <= 8GB`
  - `2: <= 16GB`
  - `3: < 64GB`

2. Memory Regressor
1D-CNN performs logistic regression to estimate how much memory (in Gigabytes) a given dataset will require for processing. This prediction is not used directly by the pipeline because AWS compute doesn't require an exact number (hence the bin classification). We retain this model for the purpose of additional analysis of the datasets and their evolving characteristics.

3. Wallclock Regressor
1D-CNN performs logistic regression to estimate the job's execution time in wallclock seconds. AWS Batch requires a minimum threshold of 60 seconds to be set on each job, although many jobs take less than one minute to complete. The predicted value from this model is used by JobSubmit to set a maximum execution time in which the job has to be completed, after which a job is killed (regardless of whether or not it has finished).

JobPredict 
--------------

The JobPredict lambda is invoked by JobSubmit to determine resource allocation needs pertaining to memory and execution time. Upon invocation, a container is created on the fly using a docker image stored in the caldp ECR. The container then loads pre-trained models along with their learned parameters (e.g. weights) from saved keras files.

The model's inputs are scraped from a text file in the calcloud-processing s3 bucket (`control/ipppssoot/MemoryModelFeatures.txt`) and converted into a numpy array. An additional preprocessing step applies a Yeo-Johnson power transform to the first two indices of the array (`n_files`, `total_mb`) using pre-calculated statistical values (mean, standard deviation and lambdas) representative of the entire training data "population". This transformation restricts all values into a 5-value range (-2 to 3) - see Model Training (below) for more details. 

The resulting 2D-array of transformed inputs are then fed into the models which generate predictions for minimum memory size and wallclock (execution) time requirements. Predicted outputs are formatted into JSON and returned back to the JobSubmit lambda to acquire the compute resources necessary for completing calibration processing on that particular ipppssoot's data.


Model Ingest
------------

When a job finishes successfully, its status message (in s3) changes to `processed-$ipppssoot.trigger`, and the  `model-ingest` lambda is automatically triggered. Similar to JobPredict lambda, the job's inputs/features are scraped from the control file in s3, in addition to the actual measured values for memory usage and wallclock time as recorded in the s3 outputs log files `process_metrics.txt | preview_metrics.txt`. The latter serve as ground truth target class labels for training the model. The features and targets are combined into a python dictionary, which is then formatted into a DynamoDB-compatible json object and ingested into the `calcloud-model` DynamoDB table for inclusion in the next model training iteration.


Model Training
--------------

Keeping the models performative requires periodic retraining with the latest available data. Unless revisions are otherwise deemed necessary, the overall architecture and tuned hyperparameters of each network are re-built from scratch using the Keras functional API, then trained and validated using all available data. Model training iterations are manually submitted via AWS batch, which fires up a Docker container from the `training` image stored in CALDP elastic container repository (ECR) and runs through the entire training process as a standalone job (separate from the main calcloud processing runs):

  1. Download training data from DynamoDB table
  2. Preprocess (calculate statisics and re-run the PowerTransform on `n_files` and `total_mb`)
  3. Build and compile models using Keras Functional API
  4. Split data into train and test (validation) sets
  5. Run batch training for each model
  6. Calculate metrics and scores for evaluation 
  7. Save and upload models and training results to s3
  8. (optional) Run KFOLD cross-validation (10 splits)


Calcloud ML Dashboard
---------------------

Analyze model performance, compare training iterations and explore statistical attributes of the continually evolving dataset with an interactive dashboard built specifically for Calcloud's prediction and classification models. The dashboard is maintained in a separate repository which can be found here: [CALCLOUD-ML-DASHBOARD](https://github.com/alphasentaurii/calcloud-ml-dashboard.git).