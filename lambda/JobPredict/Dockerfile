#FROM public.ecr.aws/lambda/python:3.6
FROM amazon/aws-lambda-python:3.7
COPY requirements.txt lambda_predict.py ./
RUN python3.7 -m pip install -r requirements.txt
ADD  models ./models/
CMD ["lambda_predict.lambda_handler"]