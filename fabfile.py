#! /usr/bin/env python2
# -*- coding: utf-8 -*-

"""The Sage Cell Server installer fabric file"""

from fabric.api import local

def live():
    """Upload package to PyPI Live"""

    local("cd /home/paad/sagecell; "
          "python setup.py register -r pypi; "
          "python setup.py sdist --format=zip,gztar upload -r pypi")

def git():
    """Setup git"""

    local("cd /home/paad/sagecell; "
          "git remote rm origin; "
          "git remote add origin https://korniichuk@github.com/korniichuk/sagecell.git; "
          "git remote add bitbucket https://korniichuk@bitbucket.org/korniichuk/sagecell.git")

def test():
    """Upload package to PyPI Test"""

    local("cd /home/paad/sagecell; "
          "python setup.py register -r pypitest; "
          "python setup.py sdist --format=zip,gztar upload -r pypitest")
