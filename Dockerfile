# Use slim Python image
FROM python:3.12.2-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt dev-requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r dev-requirements.txt \
    && pip install --upgrade ruff


# Copy source code
COPY . .

RUN pip install -e .

# Default command
ENTRYPOINT ["python", "main.py"]
