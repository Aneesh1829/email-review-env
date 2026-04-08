FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ✅ Correct: copy full project (context is root already)
COPY . /app

# ✅ FIX: requirements path is WRONG earlier
RUN pip install --no-cache-dir -r /app/requirements.txt

# Create output directories
RUN mkdir -p /app/outputs/evals /app/outputs/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Expose port
EXPOSE 7860

# Run FastAPI server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]