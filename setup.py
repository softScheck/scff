#!/usr/bin/env python3

import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

def every_file_in(folder):
    s = [folder + '/' + s for s in os.listdir(folder) \
        if os.path.isfile(folder + '/' + s)]
    return s

setup(name='scff',
    version='0.42',
    description='softScheck Cloud Fuzzing Framework',
    author='Wilfried Kirsch',
    author_email='wilfried.kirsch@softscheck.com',
    url='https://github.com/softscheck/scff',
    license='GPL v3',
    packages=['scff'],
    platforms='any',
    include_package_data=True,

    data_files=[('share/scff', every_file_in('data/scff')),
                ('share/scff/fuzzers', every_file_in('data/scff/fuzzers')),
                ('share/man/man1', every_file_in('data/man/man1')),
                # hack
                ('/usr/share/bash-completion/completions',
                every_file_in('data/bash-completion/completions')),
                ('/usr/share/zsh/vendor-completions',
                every_file_in('data/zsh/vendor-completions'))
                ],


    install_requires=['boto3'],
    scripts=every_file_in('bin'),
    classifiers = [
        'Programming Language :: Python3',
        'Development Status :: 3 - Alpha',
        'Natural Language :: English'
    ]
    )

