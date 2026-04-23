from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="arm-cloudnet-data-fetcher",
    version="0.1.0",
    author="ARM-CloudNet Data Fetcher",
    description="Automatic download toolkit for ARM and CloudNet cloud radar & vertical observation data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/arm-cloudnet-data-fetcher",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "arm-fetch=arm_cloudnet_fetcher.cli:arm_main",
            "cloudnet-fetch=arm_cloudnet_fetcher.cli:cloudnet_main",
            "data-catalog=arm_cloudnet_fetcher.cli:catalog_main",
        ],
    },
)
