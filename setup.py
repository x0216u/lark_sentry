#!/usr/bin/env python
# coding: utf-8
from setuptools import setup

from lark_sentry import __version__


with open('README.md', 'r') as f:
    long_description = f.read()


setup(
    name='lark_sentry',
    version=__version__,
    packages=['lark_sentry'],
    url='https://github.com/x0216u/lark_sentry',
    author='x0216u',
    author_email='x0216u@gmail.com',
    description='Plugin for Sentry which allows sending notification via Lark messenger.',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    license='MIT',
    entry_points={
        'sentry.plugins': [
            'lark_sentry = lark_sentry.plugin:LarkSentryNotificationsPlugin',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Bug Tracking',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: System :: Monitoring',
    ],
    install_requires=['sentry>=9.1.2'],
    include_package_data=True,
)