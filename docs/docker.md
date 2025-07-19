# Docker Deployment

Deploy TgCaller applications using Docker for consistent, scalable environments.

## Basic Dockerfile

Create a `Dockerfile` for your TgCaller application:

```dockerfile
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
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 tgcaller && \
    chown -R tgcaller:tgcaller /app

USER tgcaller

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import tgcaller; print('TgCaller OK')" || exit 1

# Default command
CMD ["python", "bot.py"]
```

## Docker Compose

Use Docker Compose for multi-service deployments:

```yaml
version: '3.8'

services:
  tgcaller-bot:
    build: .
    container_name: tgcaller-bot
    restart: unless-stopped
    environment:
      - API_ID=${API_ID}
      - API_HASH=${API_HASH}
      - BOT_TOKEN=${BOT_TOKEN}
      - PYTHONUNBUFFERED=1
    volumes:
      - ./downloads:/app/downloads
      - ./logs:/app/logs
      - ./sessions:/app/sessions
    ports:
      - "8080:8080"
    networks:
      - tgcaller-network
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    container_name: tgcaller-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - tgcaller-network

  nginx:
    image: nginx:alpine
    container_name: tgcaller-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    networks:
      - tgcaller-network
    depends_on:
      - tgcaller-bot

volumes:
  redis_data:

networks:
  tgcaller-network:
    driver: bridge
```

## Environment Configuration

Create a `.env` file for environment variables:

```env
# Telegram API credentials
API_ID=12345
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token

# Optional configurations
LOG_LEVEL=INFO
REDIS_URL=redis://redis:6379
DATABASE_URL=postgresql://user:pass@db:5432/tgcaller

# Advanced features
YOUTUBE_API_KEY=your_youtube_key
WHISPER_MODEL=base
```

## Building and Running

### Build the Image

```bash
# Build the Docker image
docker build -t tgcaller-bot .

# Build with specific tag
docker build -t tgcaller-bot:v1.0.0 .
```

### Run Single Container

```bash
# Run with environment file
docker run -d \
  --name tgcaller-bot \
  --env-file .env \
  -v $(pwd)/downloads:/app/downloads \
  -p 8080:8080 \
  tgcaller-bot

# Run with inline environment variables
docker run -d \
  --name tgcaller-bot \
  -e API_ID=12345 \
  -e API_HASH=your_hash \
  -e BOT_TOKEN=your_token \
  tgcaller-bot
```

### Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f tgcaller-bot

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

## Advanced Configuration

### Multi-Stage Build

Optimize image size with multi-stage builds:

```dockerfile
# Build stage
FROM python:3.11-slim as builder

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libffi-dev

COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
COPY . /app

WORKDIR /app
ENV PATH=/root/.local/bin:$PATH

CMD ["python", "bot.py"]
```

### Volume Mounts

Configure persistent storage:

```yaml
services:
  tgcaller-bot:
    volumes:
      # Session files
      - ./sessions:/app/sessions
      # Downloaded media
      - ./downloads:/app/downloads
      # Application logs
      - ./logs:/app/logs
      # Configuration files
      - ./config:/app/config:ro
```

### Network Configuration

```yaml
networks:
  tgcaller-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## Production Deployment

### Resource Limits

```yaml
services:
  tgcaller-bot:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Health Checks

```yaml
services:
  tgcaller-bot:
    healthcheck:
      test: ["CMD", "python", "-c", "import tgcaller; print('OK')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Logging Configuration

```yaml
services:
  tgcaller-bot:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Monitoring

### Container Monitoring

```bash
# View container stats
docker stats tgcaller-bot

# View logs
docker logs -f tgcaller-bot

# Execute commands in container
docker exec -it tgcaller-bot bash
```

### Health Monitoring

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' tgcaller-bot

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' tgcaller-bot
```

## Troubleshooting

### Common Issues

**Audio/Video not working:**
```bash
# Check if audio devices are available
docker run --rm -it --device /dev/snd tgcaller-bot aplay -l
```

**Permission errors:**
```bash
# Fix file permissions
sudo chown -R 1000:1000 ./sessions ./downloads ./logs
```

**Memory issues:**
```bash
# Increase memory limits
docker run -m 2g tgcaller-bot
```

### Debug Mode

Run container in debug mode:

```bash
docker run -it --rm \
  --env-file .env \
  tgcaller-bot \
  python -c "
import tgcaller
print('TgCaller version:', tgcaller.__version__)
print('Debug mode active')
"
```

This Docker setup provides a robust, scalable deployment solution for TgCaller applications.