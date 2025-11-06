FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY . .

# Create output directory
RUN mkdir -p reports/data

# Run the analysis script
CMD ["python", "battery_arbitrage.py"]
