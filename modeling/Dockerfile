FROM library/ubuntu:20.04
#SSL/TLS cert setup for STScI AWS firewalling
USER root
ENV REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
ENV CURL_CA_BUNDLE=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
RUN mkdir -p /etc/ssl/certs/ && mkdir -p /etc/pki/ca-trust/extracted/pem/
COPY certs/tls-ca-bundle.pem /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
RUN ln -s /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem /etc/ssl/certs/ca-bundle.crt && ln -s /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem /etc/ssl/certs/ca-certificates.crt && mkdir -p /etc/pki/ca-trust/extracted/openssl
RUN DEBIAN_FRONTEND=noninteractive && NCORES=`nproc` && apt update && apt upgrade -y && apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev liblzma-dev curl unzip && wget https://www.python.org/ftp/python/3.9.5/Python-3.9.5.tgz && tar -xf Python-3.9.5.tgz && cd Python-3.9.5 && ./configure --enable-optimizations && make -j $NCORES && make altinstall && update-alternatives --install /usr/local/bin/python python /usr/local/bin/python3.9 10 && cd ../ && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && unzip awscliv2.zip && ./aws/install

WORKDIR /home/developer
COPY requirements.txt ./
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt && mkdir -p /home/developer/modeling
ADD main.py io.py ingest.py train.py ./modeling/
CMD ["python", "-m", "modeling.main"]
