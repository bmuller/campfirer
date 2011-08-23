#!/usr/bin/env python
try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

setup(
    name="campfirer",
    version="0.1",
    description="Jabber MUC interface to campfire rooms",
    author="Brian Muller",
    author_email="bamuller@gmail.com",
    license="MIT",
    url="http://findingscience.com/campfirer",
    packages=["campfirer"],
    requires=["twisted.enterprise.adbapi", "twisted.words"]
)
