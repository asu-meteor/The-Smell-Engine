"""Setup file for Olfactometer"""

from pathlib import Path
from setuptools import setup, find_packages


def read_requirements():
    '''parses requirements from requirements.txt'''
    reqs_path = Path(__file__).parent / 'requirements.txt'
    reqs = None
    with open(reqs_path) as reqs_file:
        reqs = reqs_file.read().splitlines()
    return reqs


setup(
    name='olfactometer',
    version=0.1,
    author='Rick Gerkin, Alireza Bahremand, Mason Manetta',
    author_email='rgerkin@asu.edu',
    packages=find_packages(),
    license='MIT',
    description=("A package for controlling an olfactometer."),
    long_description="",
    install_requires=read_requirements(),
    )
