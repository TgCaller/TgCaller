#!/usr/bin/env python3
"""
TgCaller - Modern Telegram Group Calls Library
"""

import re
from setuptools import setup, find_packages

# Read version
with open("tgcaller/__init__.py", encoding="utf-8") as f:
    version = re.search(r'__version__ = "([^"]+)"', f.read()).group(1)

# Read README
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

# Read requirements
with open("requirements.txt", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="tgcaller",
    version=version,
    author="TgCaller Team",
    author_email="team@tgcaller.dev",
    description="Modern, fast, and reliable Telegram group calls library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tgcaller/tgcaller",
    project_urls={
        "Documentation": "https://tgcaller.readthedocs.io",
        "Source": "https://github.com/tgcaller/tgcaller",
        "Tracker": "https://github.com/tgcaller/tgcaller/issues",
        "Community": "https://t.me/tgcaller",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Video",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords=[
        "telegram", "calls", "voip", "streaming", "audio", "video",
        "pytgcalls", "alternative", "modern", "fast", "reliable"
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "video": [
            "opencv-python>=4.7.0",
            "imageio>=2.28.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "tgcaller=tgcaller.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)