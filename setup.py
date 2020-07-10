from setuptools import setup
import glob

setup(name='calcloud',
      version='0.1',
      description='Supports running large numbers of STScI calibration jobs on AWS.',
      url='http://github.com/spacetelescope/calcloud',
      author='STScI DMD Team Octarine',
      author_email='dmd_octarine@stsci.edu',
      license='MIT',
      packages=['calcloud'],
      scripts=glob.glob("scripts/*"),
      install_requires=["awscli", "boto3"],
      extras_require = {
          "dev" : ["black", "flake8", "bandit"],
          },
      zip_safe=False)
