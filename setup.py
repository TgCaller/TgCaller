"""TgCaller packaging metadata.

This project keeps the runtime metadata in tgcaller/__version__.py and the
packaging metadata in pyproject.toml. Keeping them aligned avoids confusing
version mismatches during install and import.
"""

from setuptools import setup


if __name__ == "__main__":
    setup()
