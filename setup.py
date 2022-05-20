from setuptools import setup

setup(
    name="run",
    version="1.0.3",
    description="python module for running experiments",
    url="https://github.com/thobl/run",
    author="Thomas Bläsius",
    author_email="thomas.blaesius@kit.edu",
    license="ISC",
    py_modules=["run"],
    install_requires=["filelock", "tqdm", "pathos"],
)
