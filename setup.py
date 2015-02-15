__author__ = 'facetoe'

from setuptools import setup

setup(name='zenbot',
      version='0.1.0',
      install_requires=['requests', 'zenpy'],
      description='IRC bot for getting information from Zendesk',
      url='https://github.com/facetoe/zenbot',
      author='facetoe',
      author_email='facetoe@ymail.com',
      license='MIT',
      packages=['zenbot'
                '.lib'],
      zip_safe=True)
