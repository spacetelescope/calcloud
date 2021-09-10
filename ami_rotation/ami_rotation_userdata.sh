Content-Type: multipart/mixed; boundary="==BOUNDARY==" 
MIME-Version: 1.0 

--==BOUNDARY==
MIME-Version: 1.0 
Content-Type: text/x-shellscript; charset="us-ascii"

#!/bin/bash -ex
exec &> >(while read line; do echo "$(date +'%Y-%m-%dT%H.%M.%S%z') $line" >> /var/log/user-data.log; done;)
# ensures instance will shutdown even if we don't reach the end
shutdown -h +20
log_stream="`date +'%Y-%m-%dT%H.%M.%S%z'`"
sleep 5

cat << EOF > /home/ec2-user/log_listener.py
import boto3
import time
import sys
from datetime import datetime
  
client = boto3.client('logs')

log_group = sys.argv[1]
log_stream = sys.argv[2]

pushed_lines = []

while True:
    response = client.describe_log_streams(
        logGroupName=log_group,
        logStreamNamePrefix=log_stream
    )
    try:
        nextToken = response['logStreams'][0]['uploadSequenceToken']
    except KeyError:
        nextToken = None
    with open("/var/log/user-data.log", 'r') as f:
        lines = f.readlines()
        new_lines = []
        for line in lines:
            if line in pushed_lines:
                continue
            timestamp = line.split(" ")[0].strip()
            try:
                dt = datetime.strptime(timestamp, "%Y-%m-%dT%H.%M.%S%z")
                dt_ts = int(dt.timestamp())*1000 #milliseconds
                if nextToken is None:
                    response = client.put_log_events(
                        logGroupName = log_group,
                        logStreamName = log_stream,
                        logEvents = [
                            {
                                'timestamp': dt_ts,
                                'message': line
                            }
                        ]
                    )
                    nextToken = response['nextSequenceToken']
                else:
                    response = client.put_log_events(
                        logGroupName = log_group,
                        logStreamName = log_stream,
                        logEvents = [
                            {
                                'timestamp': dt_ts,
                                'message': line
                            }
                        ],
                        sequenceToken=nextToken
                    )
                    nextToken = response['nextSequenceToken']
            except Exception as e:
                # print(e)
                continue

            pushed_lines.append(line)
            time.sleep(0.21) #AWS throttles at 5 calls/second
    time.sleep(2)

EOF

echo BEGIN
pwd
date '+%Y-%m-%d %H:%M:%S'

yum install -y -q gcc libpng-devel libjpeg-devel unzip yum-utils
yum update -y -q && yum upgrade -q
cd /home/ec2-user
curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -qq awscliv2.zip
./aws/install
curl -s "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
mkdir /home/ec2-user/.aws
yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo
yum install terraform-0.15.4-1 -y -q
yum install git -y -q
yum install python3 -y -q

chown -R ec2-user:ec2-user /home/ec2-user/

mkdir -p /usr/lib/ssl
mkdir -p /etc/ssl/certs
mkdir -p /etc/pki/ca-trust/extracted/pem
ln -s /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem /etc/ssl/certs/ca-certificates.crt
ln -s /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem /usr/lib/ssl/cert.pem 

python3 -m pip install -q --upgrade pip && python3 -m pip install boto3 -q

sudo -i -u ec2-user bash << EOF
mkdir ~/bin ~/tmp
cd ~/tmp
curl -s -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.34.0/install.sh | bash
bash ~/.nvm/nvm.sh
source ~/.bashrc
nvm install node
npm config set registry http://registry.npmjs.org/
npm install -g awsudo
npm config set cafile /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
cd ~
rm -rf ~/tmp
EOF

chown -R ec2-user:ec2-user /home/ec2-user/

echo "export ADMIN_ARN=${admin_arn}" >> /home/ec2-user/.bashrc
echo "export AWS_DEFAULT_REGION=us-east-1" >> /home/ec2-user/.bashrc
echo "export aws_env=${environment}" >> /home/ec2-user/.bashrc

# get cloudwatch logging going
sudo -i -u ec2-user bash << EOF
cd /home/ec2-user
source .bashrc
aws logs create-log-stream --log-group-name "${log_group}" --log-stream-name $log_stream
python3 /home/ec2-user/log_listener.py "${log_group}" $log_stream &
EOF

# calcloud checkout, need right tag
cd /home/ec2-user
mkdir ami_rotate && cd ami_rotate
git clone https://github.com/spacetelescope/calcloud.git
cd calcloud
git remote set-url origin DISABLED --push
git fetch
git fetch --all --tags && git checkout tags/v${calcloud_ver} && cd ..
git_exit_status=$?
if [[ $git_exit_status -ne 0 ]]; then
    # try without the v
    cd calcloud && git fetch --all --tags && git checkout tags/${calcloud_ver} && cd ..
    git_exit_status=$?
fi
if [[ $git_exit_status -ne 0 ]]; then
    echo "could not checkout ${calcloud_ver}; exiting"
    exit 1
fi

sudo -i -u ec2-user bash << EOF
cd /home/ec2-user
source .bashrc
cd ami_rotate/calcloud/terraform
./deploy_ami_rotate.sh
EOF

sleep 120 #let logs catch up

shutdown -h now

--==BOUNDARY==--
