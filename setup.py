# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import multiprocessing

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='SavePlus+',
    version='0.0.1',
    description='Save versioning of files in Maya',
    long_description=readme,
    author='Andres Weber',
    author_email='andresmweber@gmail.com',
    url='https://github.com/andresmweber/SavePlus-',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    test_suite='nose.collector',
    tests_require=['nose'],
    include_package_data=True,
    zip_safe=False
)
