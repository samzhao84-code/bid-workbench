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
RUN mkdir -p /app/data

# Expose port (Railway sets $PORT)
ENV PORT=8000
EXPOSE ${PORT}

# Start
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
