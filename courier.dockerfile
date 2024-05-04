FROM python:3

RUN mkdir -p opt/src/courier

WORKDIR /opt/src/courier

COPY applications/applicationCourier.py ./applicationCourier.py
COPY applications/configuration.py ./configuration.py
COPY applications/models.py ./models.py
COPY applications/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="opt/src/courier"
ENTRYPOINT ["python", "./applicationCourier.py"]