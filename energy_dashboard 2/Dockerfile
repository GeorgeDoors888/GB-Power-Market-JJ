FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8080

ENV PROJECT_ID=inner-cinema-476211-u9 \
    DATASET_ID=uk_energy_prod \
    GOOGLE_APPLICATION_CREDENTIALS=/app/creds.json

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8080"]
