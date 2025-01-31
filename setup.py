from setuptools import setup, find_packages

setup(
    name='promoai',
    version='1.0.0',
    packages=find_packages(),
    install_requires=open('requirements.txt').read().splitlines()
)
