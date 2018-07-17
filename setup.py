from setuptools import setup
import mkinx


import pypandoc
long_description = pypandoc.convert('README.md', 'rst', format='md')


setup(name='mkinx',
      author='Victor Schmidt',
      author_email='vsch@protonmail.com',
      description='Manage sphinx documentations with mkdocs',
      include_package_data=True,
      keywords='documentation doc sphinx mkdocs mkinx',
      license='GNU',
      long_description=long_description,
      packages=['mkinx'],
      scripts=['bin/mkinx'],
      url='https://github.com/entrepreneur-interet-general/mkinx',
      version=mkinx.__version__,
      zip_safe=False,
      install_requires=[
          'watchdog',
          'sphinx>=1.7.6',
          'mkdocs',
          'sphinx_rtd_theme>=0.4.0',
          'mkdocs-material',
          'pexpect',
          'pygments'
      ],
      )
