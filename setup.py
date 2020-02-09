#!/usr/bin/env python

from distutils.core import setup

setup(name='CameraStream',
      version='1.0',
      py_modules=['CameraStream'],
      description='Uses gstreamer to send low latency video over a network',
      author='Michal Adamkiewicz',
      author_email='mikadam@stanford.edu',
      url='https://github.com/stanfordroboticsclub/RoverCam',
     )

