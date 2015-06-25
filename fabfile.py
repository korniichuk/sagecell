#! /usr/bin/env python2
# -*- coding: utf-8 -*-

"""The Sage Cell Server installer fabric file"""

from fabric.api import local

def live():
    """Upload package to PyPI Live"""

    local("python setup.py register -r pypi")
    local("python setup.py sdist --format=zip,gztar upload -r pypi")

def git():
    """Setup git"""

    local("git remote rm origin")
    local("git remote add origin https://korniichuk@github.com/korniichuk/sagecell.git")
    local("git remote add bitbucket https://korniichuk@bitbucket.org/korniichuk/sagecell.git")

def test():
    """Upload package to PyPI Test"""

    local("python setup.py register -r pypitest")
    local("python setup.py sdist --format=zip,gztar upload -r pypitest")
