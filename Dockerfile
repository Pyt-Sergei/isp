FROM python:3.8.10

WORKDIR /usr/src/app

COPY . .

RUN pip install -r requirements.txt
