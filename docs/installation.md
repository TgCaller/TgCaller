# Installation

## Requirements

- Python 3.8 or higher
- FFmpeg (for media processing)
- A Telegram account and API credentials

## System Dependencies

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install ffmpeg libopus-dev libffi-dev libnacl-dev python3-dev gcc
```

### CentOS/RHEL/Fedora

```bash
sudo dnf install ffmpeg opus-devel libffi-devel libsodium-devel python3-devel gcc
```

### macOS

```bash
brew install ffmpeg opus libffi libsodium
```

### Windows

1. Download FFmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Add FFmpeg to your system PATH
3. Install Microsoft Visual C++ Build Tools

## Python Package Installation

### Basic Installation

```bash
pip install tgcaller
```

### With Media Support

```bash
pip install tgcaller[media]
```

### With Audio Processing

```bash
pip install tgcaller[audio]
```

### With Advanced Features

```bash
pip install tgcaller[advanced]
```

### Complete Installation

```bash
pip install tgcaller[all]
```

## Verify Installation

```bash
# Test installation
tgcaller test

# Check system info
tgcaller info
```

**Expected Output:**
```
🧪 Testing TgCaller installation...
✅ Pyrogram imported successfully
✅ TgCaller types imported successfully
🎉 TgCaller installation test completed successfully!
```

## Getting API Credentials

1. Go to [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Go to "API Development Tools"
4. Create a new application
5. Note down your `api_id` and `api_hash`

## Docker Installation

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
    && rm -rf /var/lib/apt/lists/*

# Install TgCaller
RUN pip install tgcaller[all]

# Copy your bot
COPY . /app
WORKDIR /app

CMD ["python", "bot.py"]
```

## Troubleshooting

### Common Issues

#### FFmpeg not found
```bash
# Check if FFmpeg is installed
ffmpeg -version

# If not installed, install it using your package manager
```

#### Permission errors on Linux
```bash
# Install in user directory
pip install --user tgcaller
```

#### Build errors on Windows
- Install Microsoft Visual C++ Build Tools
- Use pre-compiled wheels: `pip install --only-binary=all tgcaller`

#### Import errors
```bash
# Reinstall with all dependencies
pip uninstall tgcaller
pip install tgcaller[all]
```

### Getting Help

If you encounter issues:

1. Check the [GitHub Issues](https://github.com/tgcaller/TgCaller/issues)
2. Join our [Telegram Group](https://t.me/tgcaller)
3. Read the [troubleshooting guide](https://github.com/tgcaller/TgCaller/wiki/Troubleshooting)

## Development Installation

For contributing to TgCaller:

```bash
# Clone the repository
git clone https://github.com/tgcaller/TgCaller.git
cd TgCaller

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```