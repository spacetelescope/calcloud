#! /bin/sh

export PATH=/home/ec2-user/miniconda3/envs/hstdp/bin:/home/ec2-user/miniconda3/condabin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/home/ec2-user/.local/bin:/home/ec2-user/bin

#printenv
#which python

export REST_TIME=$(shuf -i 5-15 -n 1)
echo "$1 job sleeping for $REST_TIME"
sleep $REST_TIME
