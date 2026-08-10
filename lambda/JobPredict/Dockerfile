#FROM public.ecr.aws/lambda/python:3.7
FROM amazon/aws-lambda-python:3.11
COPY requirements.txt predict_handler.py models ./
# SSL/TLS cert setup for STScI AWS firewalling
USER root
# temporary. remove when nss in the base amazon image is secure again
#RUN yum update nss -y
ENV REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
ENV CURL_CA_BUNDLE=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem

RUN mkdir -p /etc/ssl/certs && mkdir -p /etc/pki/ca-trust/extracted/pem
COPY STSCICA.crt /etc/ssl/certs/STSCICA.crt
COPY STSCICA.crt /etc/pki/ca-trust/source/anchors/STSCICA.crt

RUN update-ca-trust

RUN mv /etc/ssl/certs/ca-bundle.crt /etc/ssl/certs/ca-bundle.crt.org && ln -s /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem  /etc/ssl/certs/ca-bundle.crt && ln -s /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem /etc/ssl/certs/ca-certificates.crt && mkdir -p /etc/pki/ca-trust/extracted/openssl

#log4j vuln patch
RUN yum update -y java-1.8.0-openjdk

# Update build tools.  Old pip versions cannot read modern wheel tags and will default to source builds.
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Native wheels will be fetched instantly on identical architectures
RUN pip install --no-cache-dir --only-binary=:all: \
    numpy==2.2.6 \
    scipy==1.16.3 \
    pandas==3.0.5 \
    scikit-learn==1.9.0

# Install remaining requirements
RUN python3.11 -m pip install -r requirements.txt

CMD ["predict_handler.lambda_handler"]
