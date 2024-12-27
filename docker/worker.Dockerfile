FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome and ChromeDriver for web scraping
RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get install -y chromium-chromedriver

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional worker dependencies
RUN pip install --no-cache-dir celery redis

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data email_templates

# Start Celery worker
CMD ["celery", "-A", "src.web.tasks", "worker", "--loglevel=info"]
