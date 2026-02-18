FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/backend/ src/backend/

RUN pip install --no-cache-dir . && \
    python -m spacy download en_core_web_lg

COPY examples/ examples/

EXPOSE 8000

CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
