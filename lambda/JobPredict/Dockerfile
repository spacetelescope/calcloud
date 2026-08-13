FROM amazon/aws-lambda-python:3.13
COPY requirements.txt predict_handler.py ./
COPY models ./models/

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

# Force joblib to bypass backend multiprocessing pool errors inside Lambda
ENV JOBLIB_MULTIPROCESSING=0

# Update build tools.  Old pip versions cannot read modern wheel tags and will default to source builds.
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Native wheels will be fetched instantly on identical architectures
RUN pip install --no-cache-dir --only-binary=:all: -r requirements.txt

CMD ["predict_handler.lambda_handler"]
