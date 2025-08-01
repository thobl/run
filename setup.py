from setuptools import setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="run-experiments",
    version="1.0.7",
    description="python module for running experiments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thobl/run",
    author="Thomas Bläsius",
    author_email="thomas.blaesius@kit.edu",
    license="ISC",
    py_modules=["run"],
    install_requires=["filelock", "tqdm", "pathos"],
)
