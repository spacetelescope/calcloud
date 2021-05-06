FROM library/ubuntu:20.04
#SSL/TLS cert setup for STScI AWS firewalling
USER root
ENV REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
ENV CURL_CA_BUNDLE=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
RUN mkdir -p /etc/ssl/certs/ && mkdir -p /etc/pki/ca-trust/extracted/pem/
COPY certs/tls-ca-bundle.pem /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
RUN ln -s /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem /etc/ssl/certs/ca-bundle.crt && ln -s /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem /etc/ssl/certs/ca-certificates.crt && mkdir -p /etc/pki/ca-trust/extracted/openssl
RUN apt update && apt install -y python3-dev python3-pip curl unzip && update-alternatives --install /usr/bin/python python /usr/bin/python3 10 && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && unzip awscliv2.zip && ./aws/install
WORKDIR /home/developer
COPY requirements.txt ./
RUN pip install -r requirements.txt && mkdir -p /home/developer/modeling
ADD main.py io.py ingest.py train.py ./modeling/
CMD ["python3", "-m", "modeling.main"]
