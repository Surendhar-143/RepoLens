FROM python:3.13-slim

WORKDIR /workspace

# Install system dependencies needed for git, postgres client
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements list
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose API service port
EXPOSE 8000

# Command to execute migrations and launch FastAPI via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
