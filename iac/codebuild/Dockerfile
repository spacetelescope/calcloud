# Copyright 2020-2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License"). You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#    http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file.
# This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied.
# See the License for the specific language governing permissions and limitations under the License.

FROM public.ecr.aws/amazonlinux/amazonlinux:2 

ENV AWS_DEFAULT_REGION="us-east-1"
ARG aws_env

# Install git, SSH, and other utilities
RUN set -ex \
    && yum install -y  gcc libpng-devel libjpeg-devel unzip yum-utils \ 
    && yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo \
    && yum install terraform-1.0.11 -y \
    && yum install git -y  \
    && yum install tar wget python3 which -y 
           

RUN curl -sL https://rpm.nodesource.com/setup_16.x | bash - && \
    yum install -y nodejs

ENV NODE_16_VERSION="16.15.1"

RUN npm install n -g

RUN npm config set registry http://registry.npmjs.org/ && \
    npm install -g awsudo@1.5.0
    
RUN pip3 install awscli

COPY calcloud_checkout.sh /root/

RUN chmod +x /root/calcloud_checkout.sh && /root/calcloud_checkout.sh

COPY log_listener.py /root/

ENTRYPOINT [ "/bin/bash", "-l", "-c" ]

