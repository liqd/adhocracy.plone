from setuptools import setup, find_packages
import os

version = '0.1'

long_description = (
    open('README.txt').read()
    + '\n' +
    open('CONTRIBUTORS.txt').read()
    + '\n' +
    open('CHANGES.txt').read()
    + '\n')

setup(name='adhocracy.plone',
      version=version,
      description="Plone addon to provide the adhocarcy staticpages rest api",
      long_description=long_description,
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Environment :: Web Environment",
        "Operating System :: OS Independent",
        "Framework :: Zope2",
        "Framework :: Plone",
        "Framework :: Plone :: 4.2",
        "Framework :: Plone :: 4.3",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
      ],
      keywords='',
      author='',
      author_email='',
      url='https://github.com/collective/',
      license='gpl',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      namespace_packages=['adhocracy', ],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'beautifulsoup4',
          'plone.api',
          'plone.app.dexterity',
          'plone.app.contenttypes',
          'plone.app.blocks',
          'plone.app.caching',
          # -*- Extra requirements: -*-
      ],
      extras_require={'test': ['ipdb',
                               'plone.app.testing'
                               ]
                      },
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      setup_requires=["PasteScript"],
      paster_plugins=["templer.localcommands"],
      )
