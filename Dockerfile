# QuantumTgCalls Docker Image
# Multi-stage build for optimized production image

# Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    libffi-dev \
    libssl-dev \
    libopus-dev \
    libvpx-dev \
    libsrtp2-dev \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libfreetype6-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libwebp-dev \
    libopencv-dev \
    portaudio19-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install FFmpeg from source for latest features
RUN git clone --depth 1 --branch release/6.0 https://github.com/FFmpeg/FFmpeg.git /tmp/ffmpeg && \
    cd /tmp/ffmpeg && \
    ./configure \
        --enable-shared \
        --enable-pic \
        --enable-libopus \
        --enable-libvpx \
        --enable-gpl \
        --enable-libx264 \
        --enable-libx265 \
        --disable-static \
        --disable-debug \
        --disable-doc \
        --disable-ffplay \
        --prefix=/usr/local && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    rm -rf /tmp/ffmpeg

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    QUANTUM_ENV=production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libopus0 \
    libvpx7 \
    libsrtp2-1 \
    libavformat59 \
    libavcodec59 \
    libavdevice59 \
    libavutil57 \
    libswscale6 \
    libswresample4 \
    libfreetype6 \
    libjpeg62-turbo \
    libpng16-16 \
    libtiff6 \
    libwebp7 \
    libopencv-core4.5d \
    libopencv-imgproc4.5d \
    libopencv-imgcodecs4.5d \
    portaudio19-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /usr/local/lib /usr/local/lib
COPY --from=builder /usr/local/bin/ffmpeg /usr/local/bin/
COPY --from=builder /usr/local/bin/ffprobe /usr/local/bin/

# Update library cache
RUN ldconfig

# Create non-root user
RUN groupadd -r quantum && useradd -r -g quantum quantum

# Create application directory
WORKDIR /app

# Copy application code
COPY --chown=quantum:quantum . .

# Install QuantumTgCalls
RUN pip install -e .

# Create directories for media and logs
RUN mkdir -p /app/media /app/logs /app/plugins && \
    chown -R quantum:quantum /app

# Switch to non-root user
USER quantum

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import quantumtgcalls; print('QuantumTgCalls is healthy')" || exit 1

# Expose ports (if needed for web interface)
EXPOSE 8080

# Default command
CMD ["python", "-m", "quantumtgcalls.examples.docker_example"]

# Labels
LABEL maintainer="xAI Quantum Team <quantum@xai.dev>" \
      version="1.0.0-Ω" \
      description="QuantumTgCalls - Next-generation alternative to pytgcalls" \
      org.opencontainers.image.title="QuantumTgCalls" \
      org.opencontainers.image.description="4K HDR Telegram calls with AI features" \
      org.opencontainers.image.url="https://github.com/quantumtgcalls/quantumtgcalls" \
      org.opencontainers.image.source="https://github.com/quantumtgcalls/quantumtgcalls" \
      org.opencontainers.image.version="1.0.0-Ω" \
      org.opencontainers.image.created="2025-06-20T02:30:00Z" \
      org.opencontainers.image.licenses="LGPL-3.0"