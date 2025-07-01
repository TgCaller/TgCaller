# 🤝 Contributing to TgCaller

Thank you for your interest in contributing to TgCaller! This guide will help you get started.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Style Guidelines](#style-guidelines)
- [Community](#community)

## 📜 Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you agree to uphold this code.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- FFmpeg (for media processing)
- Basic knowledge of Python and async programming

### Types of Contributions

We welcome various types of contributions:

- 🐛 **Bug Reports** - Help us identify and fix issues
- 💡 **Feature Requests** - Suggest new functionality
- 📝 **Documentation** - Improve guides and API docs
- 🧪 **Tests** - Add or improve test coverage
- 🔧 **Code** - Fix bugs or implement features
- 🎨 **Examples** - Create usage examples
- 🔌 **Plugins** - Develop community plugins

## 🛠️ Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/tgcaller.git
cd tgcaller
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install in development mode
pip install -e ".[dev]"

# Install additional dependencies for testing
pip install pytest pytest-asyncio black isort flake8 mypy
```

### 4. Verify Installation

```bash
# Run tests to verify setup
pytest tests/ -v

# Check code style
black --check tgcaller/
isort --check-only tgcaller/
flake8 tgcaller/
```

## 🔄 Making Changes

### 1. Create a Branch

```bash
# Create and switch to a new branch
git checkout -b feature/your-feature-name

# Or for bug fixes:
git checkout -b fix/issue-description
```

### 2. Make Your Changes

- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

### 3. Commit Guidelines

Use clear, descriptive commit messages:

```bash
# Good commit messages:
git commit -m "Add volume control to AudioConfig"
git commit -m "Fix memory leak in stream processing"
git commit -m "Update documentation for plugin system"

# Follow conventional commits format:
# type(scope): description
# 
# Examples:
# feat(audio): add noise suppression support
# fix(client): resolve connection timeout issue
# docs(api): update AudioConfig examples
# test(stream): add unit tests for MediaStream
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_client.py

# Run with coverage
pytest --cov=tgcaller tests/

# Run async tests only
pytest -k "async" tests/
```

### Writing Tests

- Add tests for all new functionality
- Use pytest fixtures for common setup
- Test both success and error cases
- Mock external dependencies

Example test:

```python
import pytest
from unittest.mock import Mock, AsyncMock
from tgcaller import TgCaller

class TestNewFeature:
    @pytest.fixture
    def caller(self):
        client = Mock()
        return TgCaller(client)
    
    @pytest.mark.asyncio
    async def test_new_functionality(self, caller):
        # Test implementation
        result = await caller.new_method()
        assert result is True
```

### Test Categories

- **Unit Tests** - Test individual components
- **Integration Tests** - Test component interactions
- **End-to-End Tests** - Test complete workflows
- **Performance Tests** - Test performance characteristics

## 📤 Submitting Changes

### 1. Pre-submission Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] No merge conflicts

### 2. Push Changes

```bash
# Push your branch
git push origin feature/your-feature-name
```

### 3. Create Pull Request

1. Go to the GitHub repository
2. Click "New Pull Request"
3. Select your branch
4. Fill out the PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Other (please describe)

## Testing
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

### 4. Review Process

- Maintainers will review your PR
- Address any feedback promptly
- Keep the PR updated with main branch
- Be patient and responsive

## 🎨 Style Guidelines

### Code Style

We use Black for code formatting and isort for import sorting:

```bash
# Format code
black tgcaller/
isort tgcaller/

# Check formatting
black --check tgcaller/
isort --check-only tgcaller/
```

### Python Guidelines

- Follow PEP 8
- Use type hints
- Write docstrings for public APIs
- Keep functions focused and small
- Use meaningful variable names

Example:

```python
async def join_call(
    self,
    chat_id: int,
    audio_config: Optional[AudioConfig] = None,
    video_config: Optional[VideoConfig] = None
) -> bool:
    """
    Join a voice/video call.
    
    Args:
        chat_id: Chat ID to join
        audio_config: Audio configuration
        video_config: Video configuration (optional)
        
    Returns:
        True if successful
        
    Raises:
        ConnectionError: If not connected to Telegram
        CallError: If failed to join call
    """
    # Implementation here
```

### Documentation Style

- Use clear, concise language
- Include code examples
- Document all parameters and return values
- Add usage examples for complex features

## 🏗️ Project Structure

```
tgcaller/
├── tgcaller/           # Main package
│   ├── __init__.py     # Package exports
│   ├── client.py       # Main TgCaller class
│   ├── types/          # Type definitions
│   ├── methods/        # Method implementations
│   ├── handlers/       # Event handlers
│   ├── plugins/        # Plugin system
│   └── utils/          # Utilities
├── tests/              # Test suite
├── docs/               # Documentation
├── examples/           # Usage examples
└── requirements.txt    # Dependencies
```

## 🔌 Plugin Development

### Creating Plugins

```python
from tgcaller.plugins import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"
    version = "1.0.0"
    description = "My custom plugin"
    
    async def process_audio(self, audio_frame):
        # Process audio
        return audio_frame
```

### Plugin Guidelines

- Follow the BasePlugin interface
- Handle errors gracefully
- Document plugin configuration
- Add tests for plugin functionality
- Consider performance impact

## 📚 Documentation

### Types of Documentation

- **API Reference** - Auto-generated from docstrings
- **User Guides** - Step-by-step tutorials
- **Examples** - Working code samples
- **Migration Guides** - Upgrade instructions

### Writing Documentation

- Use Markdown format
- Include code examples
- Test all code samples
- Keep examples up-to-date
- Use clear headings and structure

## 🌟 Recognition

Contributors are recognized in:

- GitHub contributors list
- Release notes
- Documentation credits
- Community highlights

## 💬 Community

### Getting Help

- **[Telegram Group](https://t.me/tgcaller)** - Real-time chat
- **[GitHub Discussions](https://github.com/tgcaller/tgcaller/discussions)** - Q&A and ideas
- **[GitHub Issues](https://github.com/tgcaller/tgcaller/issues)** - Bug reports

### Communication Guidelines

- Be respectful and inclusive
- Search existing issues before creating new ones
- Provide clear, detailed information
- Be patient with responses
- Help others when possible

## 🎯 Roadmap

Check our [project roadmap](https://github.com/tgcaller/tgcaller/projects) for:

- Planned features
- Current priorities
- Good first issues
- Help wanted items

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to TgCaller! Your efforts help make this project better for everyone. 🚀