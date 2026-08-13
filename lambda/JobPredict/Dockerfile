FROM amazon/aws-lambda-python:3.13
COPY requirements.txt predict_handler.py ./
COPY models ./models/

# SSL/TLS cert setup for STScI AWS firewalling
USER root

COPY STSCICA.crt /etc/pki/ca-trust/source/anchors/
RUN update-ca-trust

#log4j vuln patch
RUN yum update -y java-1.8.0-openjdk

# Force joblib to bypass backend multiprocessing pool errors inside Lambda
ENV JOBLIB_MULTIPROCESSING=0

# Update build tools.  Old pip versions cannot read modern wheel tags and will default to source builds.
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Native wheels will be fetched instantly on identical architectures
RUN pip install --no-cache-dir --only-binary=:all: -r requirements.txt

CMD ["predict_handler.lambda_handler"]
