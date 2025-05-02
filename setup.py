from setuptools import setup, find_namespace_packages
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

# Include package data
package_data = {
    "autoFaceFraming": [
        "config/*",
        "models/face_detector/*"
    ]
}

setup(
    name="auto-face-framing",
    version="1.0.0",
    author="Akshat Kushwaha",
    author_email="youremail@example.com",
    description="An automated face framing system that tracks faces and creates a virtual camera output",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/a3ro-dev/autoFaceFraming",
    project_urls={
        "Bug Tracker": "https://github.com/a3ro-dev/autoFaceFraming/issues",
        "Source Code": "https://github.com/a3ro-dev/autoFaceFraming",
        "Twitter": "https://twitter.com/a3rodev",
    },
    packages=find_namespace_packages(),
    include_package_data=True,
    package_data=package_data,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Video",
        "Topic :: Multimedia :: Video :: Capture",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "start-face-framing=autoFaceFraming.cli:main",
        ],
    },
)