FROM python:3.8.7-slim

ARG APP
ARG IMAGE_TAG

WORKDIR /app

RUN apt-get update

COPY ./lation/requirements.txt /app/lation/requirements.txt
RUN pip install -r /app/lation/requirements.txt
RUN apt-get autoremove -y gcc

COPY . /app

ENV APP=${APP}
ENV IMAGE_TAG=${IMAGE_TAG}

ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]

EXPOSE 8000
