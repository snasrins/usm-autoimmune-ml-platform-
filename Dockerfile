# ============================================
# USM Autoimmune ML Platform - Docker Image
# Base: NVIDIA CUDA 12.1 with cuDNN on Ubuntu 22.04
# ============================================

FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-venv \
    curl \
    git \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Install PyTorch 2.4+ with CUDA 12.1 support FIRST (before requirements.txt)
RUN pip install --no-cache-dir torch>=2.4.0 torchvision>=0.19.0 --index-url https://download.pytorch.org/whl/cu121

# Copy requirements first (for layer caching)
COPY requirements.txt /requirements.txt

# Install Python dependencies (torch already installed above)
RUN pip install --no-cache-dir -r /requirements.txt

# Download spaCy models
#RUN python -m spacy download en_core_web_sm && \
#    pip install https://s3-us-west-2.amazonaws.com/ai2-s3-scispacy/releases/v0.5.3/en_core_sci_sm-0.5.3.tar.gz

# Create necessary directories
RUN mkdir -p /data/uploads /data/processed /data/raw /models /logs

# Copy application code to /app
COPY ./app /app

# Copy Alembic configuration and migrations
COPY alembic.ini /alembic.ini
COPY ./alembic /alembic

# Copy test script
COPY ./scripts/test_gpu.py /test_gpu.py

# Set working directory to root (so Python can import 'app' package)
WORKDIR /

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV CUDA_HOME=/usr/local/cuda

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI application with Python module flag
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
