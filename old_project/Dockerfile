FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY *.py .
COPY *.json ./
COPY *.env ./

# Create directories for data
RUN mkdir -p /app/data

# Flask wrapper for ingestion services
COPY flask_wrapper.py .

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["python", "flask_wrapper.py"]
