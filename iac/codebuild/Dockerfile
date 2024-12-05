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

FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ENV AWS_DEFAULT_REGION="us-east-1"
ARG aws_env
ARG CALCLOUD_VER

RUN mkdir -p /etc/ssl/certs && \
    mkdir -p /etc/pki/ca-trust/source/anchors

COPY STSCICA.crt /etc/ssl/certs/STSCICA.crt
COPY STSCICA.crt /etc/pki/ca-trust/source/anchors/STSCICA.crt

RUN update-ca-trust

# Install git, SSH, and other utilities
RUN set -ex \
    && yum update -y --security \
    && yum install -y  gcc libpng-devel libjpeg-devel unzip yum-utils \
    && yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo \
    && yum install terraform-1.0.11 -y \
    && yum install git -y  \
    && yum install tar wget python3 which -y \
    && yum install python3-pip -y

# These should only happen once
ENV REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
ENV CURL_CA_BUNDLE=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
ENV NODE_EXTRA_CA_CERTS=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem

RUN yum install https://rpm.nodesource.com/pub_16.x/nodistro/repo/nodesource-release-nodistro-1.noarch.rpm -y
RUN yum install nodejs -y --setopt=nodesource-nodejs.module_hotfixes=1

RUN npm install n -g

RUN npm config set registry http://registry.npmjs.org/ && \
    npm install -g awsudo@1.5.0

RUN pip3 install awscli

COPY calcloud_checkout.sh /root/

RUN chmod +x /root/calcloud_checkout.sh && /root/calcloud_checkout.sh

COPY log_listener.py /root/

ENTRYPOINT [ "/bin/bash", "-l", "-c" ]