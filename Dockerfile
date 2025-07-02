FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus-dev \
    libffi-dev \
    libnacl-dev \
    python3-dev \
    gcc \
    portaudio19-dev \
    alsa-utils \
    pulseaudio \
    xvfb \
    x11vnc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 tgcaller && \
    chown -R tgcaller:tgcaller /app

USER tgcaller

# Expose ports for custom API
EXPOSE 8080

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import tgcaller; print('TgCaller OK')" || exit 1

# Default command
CMD ["python", "-m", "tgcaller.cli", "info"]