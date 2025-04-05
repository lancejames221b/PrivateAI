#!/usr/bin/env python3
"""
Private AI - Setup script

This script installs the Private AI package.
"""

from setuptools import setup, find_packages

setup(
    name="privateai",
    version="1.0.0",
    author="Lance James",
    author_email="lance@unit221b.com",
    description="Privacy protection for AI-powered development tools",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/lancejames221b/PrivateAI",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=open("requirements.txt").read().splitlines(),
    entry_points={
        "console_scripts": [
            "privateai=main:main",
        ],
    },
)
