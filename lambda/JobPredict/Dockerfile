#FROM public.ecr.aws/lambda/python:3.7
FROM amazon/aws-lambda-python:3.7
COPY requirements.txt predict_handler.py ./
RUN python3.7 -m pip install -r requirements.txt
ADD  models ./models/
CMD ["predict_handler.lambda_handler"]