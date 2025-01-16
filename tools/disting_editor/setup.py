from setuptools import setup, find_packages

setup(
    name="disting_nt",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "mido>=1.3.0",
        "python-rtmidi>=1.5.0",
        "typing>=3.7.4.3",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python interface for the Expert Sleepers Disting NT",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/disting_nt",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)