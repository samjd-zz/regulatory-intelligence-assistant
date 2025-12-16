FROM python:3.11-slim

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    antiword \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model (ignore failure if offline)
RUN python -m spacy download en_core_web_sm || true

# Copy application code
COPY . .

# Expose FastAPI port only
EXPOSE 8000

CMD ["./scripts/entrypoint_backend.sh"]
