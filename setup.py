from setuptools import setup
import glob

setup(name='hstdputils',
      version='0.1',
      description='Utilities to support HST processing',
      url='http://github.com/jaytmiller/hstdp-utils',
      author='Todd Miller',
      author_email='jmiller@stsci.edu',
      license='MIT',
      packages=['hstdputils'],
      scripts=glob.glob("scripts/*"),
      zip_safe=False)
