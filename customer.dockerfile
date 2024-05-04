FROM python:3

RUN mkdir -p opt/src/customer

WORKDIR /opt/src/customer

COPY applications/applicationCustomer.py ./applicationCustomer.py
COPY applications/configuration.py ./configuration.py
COPY applications/models.py ./models.py
COPY applications/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="opt/src/customer"
ENTRYPOINT ["python", "./applicationCustomer.py"]