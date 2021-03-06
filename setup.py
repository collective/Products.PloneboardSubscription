from setuptools import setup, find_packages
import os

version = '1.0.dev0'

tests_require = [ 'collective.MockMailHost' ]

setup(name='Products.PloneboardSubscription',
      version=version,
      description="Enables email subscription to Ploneboard posts",
      long_description=open("README.rst").read() + "\n\n\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='',
      author='Suresh V',
      author_email='suresh@grafware.com',
      url='http://plone.org/products/products.ploneboardsubscription',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
      ],
      tests_require = tests_require,
      extras_require={'test': tests_require},
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
