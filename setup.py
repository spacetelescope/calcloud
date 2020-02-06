from setuptools import setup
import glob

setup(name='hstdputils',
      version='0.1',
      description='Utilities to support HST processing',
      url='http://github.com/spacetelescope/calcloud',
      author='Todd Miller',
      author_email='jmiller@stsci.edu',
      license='MIT',
      packages=['hstdputils'],
      scripts=glob.glob("scripts/*"),
      extras_require = {
          "dev" : ["black", "flake8", "bandit"],
          },
      zip_safe=False)
