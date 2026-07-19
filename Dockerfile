FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the SentenceTransformer embeddings model to prevent first-query HTTP timeouts
RUN python -c "import os; os.environ['TRANSFORMERS_NO_TF'] = '1'; from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-large-en-v1.5')"

COPY app/ ./app/
COPY main.py ./

RUN useradd -m -u 1000 backenduser && \
    chown -R backenduser:backenduser /app
USER backenduser

ENV PORT=8000

EXPOSE ${PORT}

CMD uvicorn main:app --host 0.0.0.0 --port $PORT