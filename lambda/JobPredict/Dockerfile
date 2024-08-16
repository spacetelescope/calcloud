#FROM public.ecr.aws/lambda/python:3.7
FROM amazon/aws-lambda-python:3.11
COPY requirements.txt predict_handler.py ./
# SSL/TLS cert setup for STScI AWS firewalling
USER root
# temporary. remove when nss in the base amazon image is secure again
RUN yum update nss -y
ENV REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
ENV CURL_CA_BUNDLE=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem

RUN mkdir -p /etc/ssl/certs && mkdir -p /etc/pki/ca-trust/extracted/pem
COPY STSCICA.crt /etc/ssl/certs/STSCICA.crt
COPY STSCICA.crt /etc/pki/ca-trust/source/anchors/STSCICA.crt

RUN update-ca-trust

RUN mv /etc/ssl/certs/ca-bundle.crt /etc/ssl/certs/ca-bundle.crt.org && ln -s /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem  /etc/ssl/certs/ca-bundle.crt && ln -s /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem /etc/ssl/certs/ca-certificates.crt && mkdir -p /etc/pki/ca-trust/extracted/openssl

#log4j vuln patch
RUN yum update -y java-1.8.0-openjdk

#RUN python3.7 -m pip install --upgrade pip && python3.7 -m pip install -r requirements.txt && python3.7 -m pip install https://storage.googleapis.com/tensorflow/linux/cpu/tensorflow_cpu-2.6.2-cp37-cp37m-manylinux2010_x86_64.whl
RUN python3.11 -m pip install --upgrade pip && python3.11 -m pip install -r requirements.txt && python3.11 -m pip install tensorflow-cpu==2.12.1
ADD  models ./models/
RUN chmod -R ugo+r ./models/
CMD ["predict_handler.lambda_handler"]
