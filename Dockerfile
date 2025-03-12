FROM python:3.11-slim
RUN apt-get update \
    && apt-get install -y curl \
    && curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash -s -- -n
ENV PATH="/root/yandex-cloud/bin:${PATH}"
ENV DEBUG=True
ENV WORKDIR='/app'
ENV DB_PATH='/app/data'
ENV RESPONSES_DB_NAME=
WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app
RUN --mount=type=secret,id=yc_key,target=/app/secrets/authorized_key.json \
    bash -c /app/yc_init.sh
RUN mkdir /app/secrets && python fetch_google_creds.py
RUN mkdir /app/data && python /app/src/recreate_databases.py
# Run the application
# CMD ["which", "yc"]
CMD python ./src/recreate_databases.py && python ./src/bot.py
