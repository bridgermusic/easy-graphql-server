#!/usr/bin/env python

from re import search
from setuptools import setup, find_packages

version = '0.9.2',

with open('README.md') as readme_file:
    readme = readme_file.read()

setup(
    name='easy_graphql_server',
    version = '0.9.2',
    description='Easy to use abstraction layer for GraphQL, with support for Django ORM.',
    long_description=readme,
    long_description_content_type='text/markdown',
    keywords='graphql django',
    url='https://github.com/mathieurodic/easy-graphql-server',
    author='Mathieu Rodic',
    author_email='graphql@rodic.fr',
    license='MIT license',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    install_requires=[
        'graphql-core==3.1.7'
    ],
    extras_require={
        'tests': [
            'django==3.2',
            'faker==11.1.0',
            'flask==2.0.2',
            'flask-login==0.5.0',
        ],
    },
    python_requires='>=3.6,<4',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    # PEP-561: https://www.python.org/dev/peps/pep-0561/
    package_data={
        'easy_graphql_server': ['py.typed'],
        'easy_graphql_server.webserver.static': ['*'],
    },
    include_package_data=True,
    zip_safe=False,
)
