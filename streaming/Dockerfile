FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    kafka-python-ng==2.2.3 \
    redis==5.0.1 \
    requests==2.31.0 \
    sqlalchemy==2.0.30 \
    psycopg[binary]==3.1.18 \
    pandas==2.2.2 \
    numpy==1.26.4 \
    python-dotenv==1.0.1

COPY streaming/ /app/

CMD ["python", "consumer.py"]
