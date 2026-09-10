FROM amazon/aws-lambda-python:3.11
COPY lambda/JobPredict/requirements.txt lambda/JobPredict/predict_handler.py ./
COPY lambda/JobPredict/models ./models/
COPY calcloud ./calcloud

# SSL/TLS cert setup for STScI AWS firewalling
USER root

COPY lambda/JobPredict/STSCICA.crt /etc/pki/ca-trust/source/anchors/
RUN update-ca-trust

# Force joblib to bypass backend multiprocessing pool errors inside Lambda
ENV JOBLIB_MULTIPROCESSING=0

# Update build tools.  Old pip versions cannot read modern wheel tags and will default to source builds.
RUN pip3.11 install --no-cache-dir --upgrade pip setuptools wheel

# Native wheels will be fetched instantly on identical architectures
RUN pip3.11 install --no-cache-dir --only-binary=:all: -r requirements.txt

CMD ["predict_handler.lambda_handler"]
