FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    default-jre \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy parser requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules (if needed, but worker usually self-contained or mounts shared)
# For now, simplistic worker
COPY . .

# Environment
ENV PYTHONUNBUFFERED=1

CMD ["python", "worker.py"]
