FROM python:3

RUN mkdir -p /opt/src/authentication
WORKDIR /opt/src/authentication

COPY ./authentication/migrate.py ./migrate.py
COPY ./authentication/models.py ./models.py
COPY ./authentication/configuration.py ./configuration.py
COPY ./requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt
ENV PYTHONPATH="opt/src/authentication"

ENTRYPOINT ["python", "./migrate.py"]