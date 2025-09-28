# Shared Base Image for Multimodal LLM Stack Services
# This image contains common system dependencies to avoid repeated downloads
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install common system dependencies in a single layer
# This avoids repeated apt-get updates across services
RUN apt-get update && apt-get install -y \
    # Build tools
    build-essential \
    gcc \
    g++ \
    make \
    # System utilities
    curl \
    wget \
    git \
    # Media processing
    ffmpeg \
    # Graphics libraries
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    libgl1 \
    # Database client
    libpq-dev \
    # Clean up
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create common directories
RUN mkdir -p /app/cache /app/logs

# Set working directory
WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# This base image is designed to be extended by individual services
# Each service will copy their specific requirements and code
