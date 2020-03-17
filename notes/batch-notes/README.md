# AWS Batch Related Notes

## Batch Env JSON dumps

Currently, just JSON AWS CLI "describes" of AWS Batch resources
created with AWS wizards to use for Q&A if needed when creating future
environments.  Just docmentation,  don't think these can be used
as-is to rebuild the env.

## Batch Instance and EBS Tagging

The Compute Environment console wizard supports supplying an EC2 launch
template.  Within the launch template,  it is possible to tag both EC2
instances and their associated EBS volumes for use in costing test runs.

Some hours later Batch seems to be auto-generating it's own templates
e.g. Batch-lt-cfba3e2e-c825-36ab-b178-7611e7622ba3
derived from hstdp-batch-instance-template.  These seem to disappear
when the associated cluster instances are terminated.

## Mass Job Deletion (Delete the Queue)

At some point you're going to want to delete all jobs in the queue.

Neither the AWS console nor the CLI is good at this...  which is pretty
stressful if you have a large cluster going haywire.

Solution: Tearing down the Batch environment works well, but you need to do it
in this order: first disable and delete the queue, then disable and delete the
compute environment if needed.  Afterward, recreate them.  Deleting the queue
is sufficient to terminate all jobs and it is simple to recreate the queue.
Deleting the compute environment may be needed to minimize compute fees and
completely shut down quickly but they should also automatically tear down after
a brief idle period.

## Container "thin poll" exhaustion

The default ECS images used by Batch keep completed Docker containers
around on disk for 3 hours.  With a large enough number of jobs,  the
worker node's disk (?) fills up with stopped containers and further
job launches fail before the container can be launched.

ECS environment control variables can be set in the launch template
"user data" by entering a MIME encoded bash script, those kidders!

```
Content-Type: multipart/mixed; boundary="==BOUNDARY=="
MIME-Version: 1.0

--==BOUNDARY==
MIME-Version: 1.0
Content-Type: text/x-shellscript; charset="us-ascii"

#!/bin/bash

echo ECS_ENGINE_TASK_CLEANUP_WAIT_DURATION=1m>>/etc/ecs/ecs.config

yum update -y

```

For some reason aws ec2 describe-launch-template is not capturing the user data,
it may be a security issue or just growing pains.

Note that I threw in "yum update -y" after logging into some running cluster
instances and seeing yum security earnings and  package update offerings.
Since this is just for the "docker engine" I think tracking the latest stuff
automatically is probably a decent bet.

## Airflow Prototyping

Incomplete prototyping with Airflow for AWS Batch based on development
version of Airflow.
