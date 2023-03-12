#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

from porter import __version__

with open("README.md", encoding="utf-8") as readme_file:
    readme = readme_file.read()

with open("requirements.txt", encoding="utf-8") as requirements_file:
    requirements = requirements_file.read().splitlines(keepends=False)

with open("LICENSE", encoding="utf-8") as license_file:
    license_content = license_file.read()

setup(
    name="porter",
    version=__version__,
    description=("A command-line utility that migrate data and cache into Redis"),
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Zhiwei Wang",
    author_email="nopakring188@gmail.com",
    url="https://github.com/zhiweio/porter",
    packages=find_packages(),
    package_data={"porter": ["templates/*.yaml", "README.md"]},
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=requirements,
    license=license_content,
    zip_safe=False,
    keywords=["porter", "Redis", "MySQL", "MongoDB", "JSON", "CSV"],
    entry_points={"console_scripts": ["porter = porter.__main__:main"]},
)
