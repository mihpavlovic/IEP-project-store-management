FROM python:3

RUN mkdir -p /opt/src/applications
WORKDIR /opt/src/applications

COPY ./applications/migrate.py ./migrate.py
COPY ./applications/models.py ./models.py
COPY ./applications/configuration.py ./configuration.py
COPY ./applications/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt
ENV PYTHONPATH="opt/src/applications"

ENTRYPOINT ["python", "./migrate.py"]