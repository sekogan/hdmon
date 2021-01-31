from distutils.core import setup

from setuptools import find_packages

with open("README.md") as f:
    readme = f.read()


setup(
    name="hdmon",
    version="0.3.0",
    packages=find_packages(),
    url="https://github.com/sekogan/hdmon",
    license="GPL-3.0",
    author="Sergei Kogan",
    author_email="sekogan@gmail.com",
    description="Hard Disk Monitor",
    long_description=readme,
    install_requires=[
        "pyyaml",
    ],
    entry_points={
        "console_scripts": [
            "hdmon=hdmon.service:main",
            "hdmon-install=hdmon.setup:install",
            "hdmon-uninstall=hdmon.setup:uninstall",
        ]
    },
)
