FROM library/ubuntu:20.04
#SSL/TLS cert setup for STScI AWS firewalling
USER root
RUN mkdir -p /etc/ssl/certs/ && mkdir -p /usr/local/share/ca-certificates/ && mkdir -p /etc/pki/ca-trust/extracted/pem/
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
COPY STSCICA.crt /etc/ssl/certs/STSCICA.crt
COPY STSCICA.crt /usr/local/share/ca-certificates/STSCICA.crt
RUN apt-get update && \
    apt-get install -y ca-certificates 
RUN update-ca-certificates
RUN ln -sf /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-bundle.crt \
&& mkdir -p /etc/pki/ca-trust/extracted/openssl

RUN DEBIAN_FRONTEND=noninteractive && apt update && apt upgrade -y && apt install -y \
build-essential \
curl \
libbz2-dev \
libffi-dev \
libgdbm-dev \
liblzma-dev \
libncurses5-dev \
libnss3-dev \
libreadline-dev \
libsqlite3-dev \
libssl-dev \
unzip \
zlib1g-dev 

RUN DEBIAN_FRONTEND=noninteractive \
&& curl -o Python-3.11.5.tgz https://www.python.org/ftp/python/3.11.5/Python-3.11.5.tgz \
&& tar -xf Python-3.11.5.tgz \
&& cd Python-3.11.5 \
&& ./configure --enable-optimizations \
&& make altinstall \
&& update-alternatives --install /usr/local/bin/python python /usr/local/bin/python3.11 10 

RUN DEBIAN_FRONTEND=noninteractive \
&& cd ../ && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
&& unzip awscliv2.zip \
&& ./aws/install

RUN useradd --create-home --shell /bin/bash developer
USER developer
WORKDIR /home/developer
COPY requirements.txt ./
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt && mkdir -p /home/developer/modeling
ADD io.py main.py prep.py train.py validate.py ./modeling/
CMD ["python", "-m", "modeling.main"]
