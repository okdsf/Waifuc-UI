#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图像处理工具安装脚本
"""
from setuptools import setup, find_packages

setup(
    name="image_processor",
    version="1.0.0",
    description="基于waifuc库的图像处理应用程序",
    author="",
    author_email="",
    url="",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "waifuc",
        "PyQt5>=5.15.0",
        "Pillow>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "image_processor=src.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Multimedia :: Graphics",
    ],
    python_requires=">=3.8",
)
