FROM python:3.13-slim

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements list
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker source
COPY . .

# Run ARQ worker
CMD ["arq", "app.main.WorkerSettings"]
