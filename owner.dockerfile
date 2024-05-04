FROM python:3

RUN mkdir -p opt/src/owner

WORKDIR /opt/src/owner

COPY applications/applicationOwner.py ./applicationOwner.py
COPY applications/configuration.py ./configuration.py
COPY applications/models.py ./models.py
COPY applications/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="opt/src/customer"
ENTRYPOINT ["python", "./applicationOwner.py"]