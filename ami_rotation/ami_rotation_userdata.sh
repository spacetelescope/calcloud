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
cd ~
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
mkdir ~/.aws
yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo
yum install terraform-0.15.4-1 -y
yum install git -y
yum install python3 -y

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

ADMIN_ARN=${admin_arn}
AWS_DEFAULT_REGION=us-east-1

# calcloud checkout, need right tag
cd ~
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

cd calcloud/terraform
aws_env=${environment}
sudo -i -u ec2-user bash << EOF
bash deploy_ami_rotate.sh
EOF

# shutdown -h now

--==BOUNDARY==--