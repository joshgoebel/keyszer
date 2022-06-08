#!/usr/bin/env python

from setuptools import setup, find_packages
exec(open("keyszer/info.py").read())

dependencies = [
      "evdev", 
      "python-xlib", 
      "inotify_simple", 
      "appdirs",
      "ordered_set"
]

setup(name             = "keyszer",
      version          = __version__,
      author           = "Josh Goebel",
      url              = "https://github.com/jgoebel/keyszer",
      description      = __description__,
      long_description = __doc__,
      packages         = find_packages(),
      scripts          = ["bin/keyszer"],
      license          = "GPL",
      install_requires = dependencies,
      extras_require={
            "dev": [
                  "pytest",
                  "pytest-asyncio",
                  "looptime"
            ]
      }
      )
