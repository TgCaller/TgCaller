# TgCaller CLI

The TgCaller Command Line Interface provides powerful tools for testing, diagnostics, and managing your TgCaller installations.

## Installation

The CLI is automatically installed with TgCaller:

```bash
pip install tgcaller
```

## Available Commands

### Test Installation

Test your TgCaller installation and verify all components are working:

```bash
# Basic test
tgcaller test

# Test with API credentials
tgcaller test --api-id 12345 --api-hash "your_api_hash"
```

**Expected Output:**
```
🧪 Testing TgCaller installation...
✅ Pyrogram imported successfully
✅ TgCaller types imported successfully
🎉 TgCaller installation test completed successfully!
```

### System Information

Display detailed system information and dependency status:

```bash
tgcaller info
```

This shows:
- TgCaller version
- Python version and platform details
- Dependency status (required and optional)
- System architecture information

### Diagnostics

Run comprehensive diagnostic checks:

```bash
tgcaller diagnose
```

Provides:
- Complete system analysis
- Missing dependency detection
- Installation recommendations
- Performance insights

### Show Examples

Display usage examples and code snippets:

```bash
tgcaller examples
```

### Help and Version

```bash
# Show help
tgcaller --help

# Show version
tgcaller --version

# Show links
tgcaller links
```

## CLI Options

### Global Options

- `--version` - Show TgCaller version
- `--no-banner` - Don't show the ASCII banner
- `--help` - Show help information

### Test Command Options

- `--api-id` - Your Telegram API ID
- `--api-hash` - Your Telegram API Hash

## Examples

### Complete Installation Test

```bash
# Test everything with your credentials
tgcaller test --api-id 12345 --api-hash "abcdef123456"
```

### Quick System Check

```bash
# Check if all dependencies are installed
tgcaller info
```

### Troubleshooting

```bash
# Run full diagnostics
tgcaller diagnose
```

## Troubleshooting CLI Issues

### Command Not Found

If `tgcaller` command is not found:

```bash
# Install with user flag
pip install --user tgcaller

# Or use python module
python -m tgcaller.cli --help
```

### Permission Errors

On some systems, you might need:

```bash
# Use sudo (Linux/Mac)
sudo pip install tgcaller

# Or install in user directory
pip install --user tgcaller
```

### Missing Dependencies

The CLI will show which dependencies are missing:

```bash
tgcaller diagnose
```

Follow the recommendations to install missing components.

## Advanced Usage

### Scripting

You can use the CLI in scripts:

```bash
#!/bin/bash

# Check if TgCaller is properly installed
if tgcaller test --no-banner; then
    echo "TgCaller is ready!"
    python my_bot.py
else
    echo "TgCaller installation issues detected"
    exit 1
fi
```

### CI/CD Integration

Use in continuous integration:

```yaml
# GitHub Actions example
- name: Test TgCaller
  run: |
    pip install tgcaller
    tgcaller test --no-banner
```

The CLI provides comprehensive tools for managing your TgCaller development workflow efficiently.