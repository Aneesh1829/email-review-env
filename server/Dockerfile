# Dockerfile
# ----------
# Packages the environment as a container for Hugging Face Spaces.
# Must expose port 7860 for HF Spaces (they redirect 80→7860).

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire project
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/server/requirements.txt

# Create output directories
RUN mkdir -p /app/outputs/evals /app/outputs/logs

# Health check — Hugging Face Spaces pings /health
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Expose port 7860 (required for HF Spaces)
EXPOSE 7860

# Run the FastAPI server
# Note: HF Spaces uses port 7860 by default
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
