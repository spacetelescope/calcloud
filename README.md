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
Gateway between AWS and on permise NFS by flushing the cache.  Flush rates
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

2. DockerError             -

3. Job Cancelled           - An operator cancelled the job so it should not be retried.

4. Other errors            - No automatic rescue


Blackboard
==========


Job Memory Model
================

Overview
--------

... describe key aspects of the ML here such as features and network layout ...

Job Submission
--------------

Describe model execution, lambda, image, etc.

Model Training
--------------

Describe training, scraping, architecture

Dashboard?
----------
