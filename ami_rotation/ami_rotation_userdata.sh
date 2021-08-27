Content-Type: multipart/mixed; boundary="==BOUNDARY==" 
MIME-Version: 1.0 

--==BOUNDARY==
MIME-Version: 1.0 
Content-Type: text/x-shellscript; charset="us-ascii"

#!/bin/bash -ex

exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
sleep 5
echo BEGIN
date '+%Y-%m-%d %H:%M:%S'

yum install -y gcc libpng-devel libjpeg-devel unzip yum-utils
yum update -y && yum upgrade
cd /home/ec2-user
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
mkdir /home/ec2-user/.aws
yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo
yum install terraform-0.15.4-1 -y
yum install git -y
yum install python3 -y

chown -R ec2-user:ec2-user /home/ec2-user/

mkdir -p /usr/lib/ssl
mkdir -p /etc/ssl/certs
mkdir -p /etc/pki/ca-trust/extracted/pem
ln -s /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem  /etc/ssl/certs/ca-certificates.crt
ln -s /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem /usr/lib/ssl/cert.pem 

sudo -i -u ec2-user bash << EOF
mkdir ~/bin ~/tmp
cd ~/tmp
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.34.0/install.sh | bash
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

cd /home/ec2-user/

echo "export ADMIN_ARN=${admin_arn}" >> /home/ec2-user/.bashrc
echo "export AWS_DEFAULT_REGION=us-east-1" >> /home/ec2-user/.bashrc
echo "export aws_env=${environment}" >> /home/ec2-user/.bashrc

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

# shutdown -h now

--==BOUNDARY==--