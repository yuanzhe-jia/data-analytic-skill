"""
Data Analytic Skill - Setup Configuration
"""
import os
from setuptools import setup, find_packages

_here = os.path.abspath(os.path.dirname(__file__))
_readme_path = os.path.join(_here, "..", "..", "README.md")
if os.path.exists(_readme_path):
    with open(_readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "Data Analytic Skill - A planning framework for data analysis."

setup(
    name="data-analytic-skill",
    version="1.0.0",
    author="Data Science Team",
    author_email="data-science@example.com",
    description="A data analysis skill framework for decomposing complex business questions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/data-analytic-skill",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies required
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
)