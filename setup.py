#!/usr/bin/env python3
"""
QuantumTgCalls - Next-generation alternative to pytgcalls
Copyright (C) 2025 xAI Quantum Team

This file is part of QuantumTgCalls.

QuantumTgCalls is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

QuantumTgCalls is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.
"""

import re
from setuptools import setup, find_packages

# Read version from __init__.py
with open("quantumtgcalls/__init__.py", encoding="utf-8") as f:
    version = re.search(r'__version__ = "([^"]+)"', f.read()).group(1)

# Read README for long description
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

# Read requirements
with open("requirements.txt", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="quantumtgcalls",
    version=version,
    author="xAI Quantum Team",
    author_email="quantum@xai.dev",
    description="Next-generation alternative to pytgcalls with 4K HDR, AI features, and quantum-level complexity",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/quantumtgcalls/quantumtgcalls",
    project_urls={
        "Documentation": "https://quantumtgcalls.readthedocs.io",
        "Source": "https://github.com/quantumtgcalls/quantumtgcalls",
        "Tracker": "https://github.com/quantumtgcalls/quantumtgcalls/issues",
        "Community": "https://t.me/quantumtgcalls",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
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
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords=[
        "telegram", "calls", "voip", "webrtc", "streaming", "audio", "video",
        "4k", "hdr", "ai", "quantum", "pytgcalls", "alternative", "plugins"
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
            "sphinx>=4.5.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "gpu": [
            "cupy-cuda11x>=10.0.0",
            "opencv-python-headless[gpu]>=4.7.0",
        ],
        "ai": [
            "torch>=1.13.0",
            "torchaudio>=0.13.0",
            "transformers>=4.20.0",
            "speechrecognition>=3.10.0",
        ],
        "full": [
            "cupy-cuda11x>=10.0.0",
            "opencv-python-headless[gpu]>=4.7.0",
            "torch>=1.13.0",
            "torchaudio>=0.13.0",
            "transformers>=4.20.0",
            "speechrecognition>=3.10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "quantumtgcalls=quantumtgcalls.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "quantumtgcalls": [
            "ai/models/*.pth",
            "plugins/templates/*.py",
            "assets/*.json",
        ],
    },
    zip_safe=False,
)