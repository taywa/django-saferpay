#!/usr/bin/env python

from saferpay import VERSION

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='saferpay',
    packages=['saferpay'],
    version=VERSION,
    license='MIT',
    description='Saferpay payment integration for django.',
    author='Yves Serrano',
    author_email='ys@taywa.ch',
    url='https://github.com/taywa/django-saferpay',
    keywords=['saferpay', 'payment'],
    install_requires=[
        'Django>=1.11,<2.0',
    ],
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
    ],
)
