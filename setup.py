#############################################
# File Name: setup.py
# Author: rubbish
#############################################

from setuptools import find_packages, setup

setup(
    name="compensating-transaction",
    version="0.0.2",
    keywords=("pip", "compensating-transaction", "atomicity"),
    description="compensating transaction",
    long_description="When the function execution fails, the function execution can be rolled back, and all previous function executions can be rolled back",
    license="MIT Licence",
    url="https://github.com/rubbish822/compensating-transaction",
    author="rubbish",
    author_email="rubbish@rubbish.com",
    packages=find_packages(),
    include_package_data=True,
    platforms="any",
)
