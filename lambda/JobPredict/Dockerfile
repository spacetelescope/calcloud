FROM amazon/aws-lambda-python:3.12
COPY requirements.txt predict_handler.py ./
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

#RUN mv /etc/ssl/certs/ca-bundle.crt /etc/ssl/certs/ca-bundle.crt.org && ln -s /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem  /etc/ssl/certs/ca-bundle.crt && ln -s /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem /etc/ssl/certs/ca-certificates.crt && mkdir -p /etc/pki/ca-trust/extracted/openssl

#log4j vuln patch
RUN yum update -y java-1.8.0-openjdk

RUN python3.12 -m pip install --upgrade pip && python3.12 -m pip install -r requirements.txt && python3.12 -m pip install tensorflow-cpu==2.13.0
ADD  models ./models/
RUN chmod -R ugo+r ./models/
RUN find ./models/ -type d -exec chmod og+x {} +
CMD ["predict_handler.lambda_handler"]
