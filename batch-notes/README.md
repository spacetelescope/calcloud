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

## Airflow Prototyping

Incomplete prototyping with Airflow for AWS Batch based on development
version of Airflow.
