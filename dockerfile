# FROM python:3.11-slim


# WORKDIR /app

# COPY requirements.txt .

# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# CMD ["python", "main.py"]

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Limita o processo Python a ~4 GB de RAM
CMD ["bash", "-c", "ulimit -v 4194304 && python main.py"]