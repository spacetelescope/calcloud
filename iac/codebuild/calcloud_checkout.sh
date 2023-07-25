#!/bin/bash

calcloud_ver_ssm=$(aws ssm get-parameter --name /tf/env/awsysver-$aws_env --output text | cut -f 7)
calcloud_ver=${CALCLOUD_VER:-$calcloud_ver_ssm}

# calcloud checkout, need right tag
mkdir -p /opt/calcloud/ami_rotate && cd /opt/calcloud/ami_rotate
git clone https://github.com/spacetelescope/calcloud.git
cd calcloud
git remote set-url origin DISABLED --push
git fetch
git fetch --all --tags && git checkout tags/$calcloud_ver && cd ..
git_exit_status=$?
if [[ $git_exit_status -ne 0 ]]; then
    # try without the v
    cd calcloud && git fetch --all --tags && git checkout tags/$calcloud_ver && cd ..
    git_exit_status=$?
fi
if [[ $git_exit_status -ne 0 ]]; then
    echo "could not checkout $calcloud_ver; exiting"
    exit 1
fi
