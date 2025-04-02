#!/usr/bin/env python3

from setuptools import setup

if __name__ == "__main__":
    setup(
        package_dir={"": "src"},
        package_data={"helpers": ["py.typed"]},
    )