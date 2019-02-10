#!/usr/bin/env python

from saferpay import VERSION
from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name='django-saferpay',
    packages=find_packages(),
    version=VERSION,
    license='MIT',
    description='Saferpay payment integration for django.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Yves Serrano',
    author_email='ys@taywa.ch',
    url='https://github.com/taywa/django-saferpay',
    keywords=['saferpay', 'payment'],
    install_requires=[
        'Django>=1.11,<2.2',
    ],
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
    ],
)
