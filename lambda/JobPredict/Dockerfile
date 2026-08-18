#FROM public.ecr.aws/lambda/python:3.7
FROM amazon/aws-lambda-python:3.11
COPY requirements.txt predict_handler.py ./
COPY models ./models/

# SSL/TLS cert setup for STScI AWS firewalling
USER root

COPY STSCICA.crt /etc/pki/ca-trust/source/anchors/
RUN update-ca-trust

# Force joblib to bypass backend multiprocessing pool errors inside Lambda
ENV JOBLIB_MULTIPROCESSING=0

#RUN python3.7 -m pip install --upgrade pip && python3.7 -m pip install -r requirements.txt && python3.7 -m pip install https://storage.googleapis.com/tensorflow/linux/cpu/tensorflow_cpu-2.6.2-cp37-cp37m-manylinux2010_x86_64.whl
# Install numpy, h5py, scipy, and ml_dtypes first from wheels so later deps don't trigger source builds (no gcc in image).
RUN python3.11 -m pip install --upgrade pip && python3.11 -m pip install "numpy>=1.23,<2" "h5py==3.10.0" "scipy==1.11.4" "ml_dtypes==0.5.1"
RUN python3.11 -m pip install -r requirements.txt
CMD ["predict_handler.lambda_handler"]
