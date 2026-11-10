# Standalone AI demo service. Build from services/intelligence/.
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app/services/intelligence
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python scripts/run_pipeline.py --regenerate-data
EXPOSE 8001
HEALTHCHECK CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8001/health')" || exit 1
CMD ["uvicorn", "src.inference.api:app", "--host", "0.0.0.0", "--port", "8001"]
