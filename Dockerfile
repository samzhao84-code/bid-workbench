FROM python:3.11-slim

WORKDIR /app

# Install system deps for python-docx + lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Create data directory for uploads/outputs
RUN mkdir -p /app/data /app/data/tasks /app/data/uploads /app/data/outputs

# Expose port (Railway sets $PORT)
ENV PORT=8000
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8000}/api/health')" || exit 1

# Start
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
