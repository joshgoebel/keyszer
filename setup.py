#!/usr/bin/env python

from setuptools import setup
exec(open("xkeysnail/info.py").read())

dependencies = [
      "evdev", 
      "python-xlib", 
      "inotify_simple", 
      "appdirs",
      "ordered_set"
]

setup(name             = "xkeysnail",
      version          = __version__,
      author           = "Josh Goebel",
      url              = "https://github.com/jgoebel/xkeysnail",
      description      = __description__,
      long_description = __doc__,
      packages         = ["xkeysnail"],
      scripts          = ["bin/xkeysnail"],
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
