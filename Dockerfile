FROM python:3.8-slim

ARG APP

WORKDIR /app

RUN apt-get update

# for postgres
RUN apt-get install -y libpq-dev gcc

COPY ./lation/requirements.txt /app/lation/requirements.txt
RUN pip install -r /app/lation/requirements.txt
RUN apt-get autoremove -y gcc

COPY . /app

ENV APP=${APP}

ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]

EXPOSE 8000
