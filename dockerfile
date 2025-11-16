# FROM python:3.11-slim


# WORKDIR /app

# COPY requirements.txt .

# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# CMD ["python", "main.py"]

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATASET_PATH=/data/datasetcovid.zip \
    HOST_DATASET=/Users/raphaelportela/datasetcovid.zip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash", "-c", "ulimit -v 10485760 && python main_etl.py"]