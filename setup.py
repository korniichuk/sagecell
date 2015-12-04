# -*- coding: utf-8 -*-

from os.path import dirname, join
from setuptools import setup

setup(
    author = "Ruslan Korniichuk",
    author_email = "ruslan.korniichuk@gmail.com",
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        "License :: Public Domain",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 2 :: Only",
        "Topic :: Scientific/Engineering",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities"
    ],
    description = "The SageMathCell installer",
    download_url = "https://github.com/korniichuk/sagecell/archive/0.3.zip",
    entry_points = {
        'console_scripts': 'sagecell = sagecell.sagecell:main'
    },
    include_package_data = True,
    install_requires = [
        "configobj",
        "fabric"
    ],
    keywords = ["installer", "python2", "sagecell", "sagemathcell"],
    license = "Public Domain",
    long_description = open(join(dirname(__file__), "README.rst")).read(),
    name = "sagecell",
    packages = ["sagecell"],
    platforms = ["Linux"],
    scripts=['scripts/sagecellscript'],
    url = "https://github.com/korniichuk/sagecell",
    version = "0.3rc6",
    zip_safe = True
)
