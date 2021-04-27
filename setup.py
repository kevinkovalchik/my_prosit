'''
This file modified by Kevin Kovalchik
'''

from setuptools import setup, find_packages

setup(
    name="prysit",
    version="1.0",
    description="prediction",
    url="http://github.com/kusterlab/prosit",
    author="Siegfried Gessulat",
    author_email="s.gessulat@gmail.com",
    packages=find_packages(),
    zip_safe=False,
    install_requires=['tensorflow', 'keras', 'pandas', 'h5py', 'tables', 'flask', 'pyteomics', 'lxml', 'requests'],
    setup_requires=["pytest-runner"],
    tests_require=["pytest", "pylint"],
)
