# Dockerfile

# pull the official docker image
FROM python:3.9.6-buster

# set work directory
WORKDIR /app

# set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

FROM nginx:latest

COPY nginx.conf /etc/nginx/nginx.conf
# install system dependencies
# RUN apt-get update \
#     && apt-get -y install netcat gcc vim nano\
#     && apt-get clean

# install python dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt