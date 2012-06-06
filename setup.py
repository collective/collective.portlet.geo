# -*- coding: utf-8 -*-

import os, sys
from setuptools import setup, find_packages

version = '1.0.1'

install_requires = [
    'setuptools',
]

setup(name='collective.portlet.geo',
      version=version,
      description="Wrap any Plone portlet with geolocation or language negotiation.",
      long_description=open("README.rst").read() + "\n" +
                       open("CHANGES.rst").read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
        "Framework :: Zope3",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='plone portlet geolocation',
      author='Malthe Borch',
      author_email='mborch@gmail.com',
      url='http://plone.org/products/collective.portlet.geo',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective', 'collective.portlet'],
      include_package_data=True,
      zip_safe=False,
      install_requires = install_requires,
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
