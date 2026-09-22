FROM python:3.11-slim

WORKDIR /app

# Upgrade pip and install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Command to execute full FTSE 100 stock screener analysis
CMD ["python", "ftse100_screener.py", "--threads", "12", "--creds", "service_account.json"]
