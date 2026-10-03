FROM python:3.12-slim

WORKDIR /app

# System deps: none required — faiss-cpu, sentence-transformers, and torch
# all ship manylinux wheels for this base image, so no compiler toolchain
# needed. Keeping the image lean on purpose.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Runtime data — uploads, the FAISS index, and document metadata — is meant
# to be mounted as a volume in docker-compose.yml so it survives container
# restarts/rebuilds; this just guarantees the directories exist even if run
# standalone without a volume mounted.
RUN mkdir -p data/uploads data/vectorstore data/metadata

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
