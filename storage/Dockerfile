FROM ubuntu:22.04
LABEL maintainer=istewart17@my.bcit.ca
RUN apt-get update -y && \
    apt-get install -y python3 python3-pip
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install -r requirements.txt
COPY ./app.py /app/
COPY ./app_conf.yml /app/
COPY ./log_conf.yml /app/
COPY ./openapi.yml /app/
COPY ./create_database_mysql.py
COPY ./drop_tables.py

ENTRYPOINT ["python3"]
CMD ["app.py"]