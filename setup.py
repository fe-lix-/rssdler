#!/usr/bin/env python
import os
from distutils.core import setup
from distutils.command.build_scripts import build_scripts

import rssdler

if os.name == "nt":
    class build_scripts_rename(build_scripts):
        """Renames scripts so they end with '.py' on Windows."""
        def run(self):
            build_scripts.run(self)
            for f in os.listdir(self.build_dir):
                fpath = os.path.join(self.build_dir, f)
                if not fpath.endswith('.py'):
                    if os.path.exists(fpath + '.py'):  os.unlink(fpath + '.py')
                    os.rename(fpath, fpath + '.py')
else: build_scripts_rename = build_scripts

setup(
    name = 'rssdler',
    version = rssdler.getVersion(),
    description = rssdler.__doc__ ,
    long_description = """RSSDler - A Broadcatching Script
    Handles all RSS feeds supported by feedparser 0.9x, 1.0, and 2.0; CDF; and
    Atom 0.3 and 1.0
    Required: Python 2.4 or later
    Required: feedparser 
    Recommended: mechanize""",
    author = 'lostnihilist',
    author_email = 'lostnihilist@gmail.com',
    url = 'http://code.google.com/p/rssdler/',
    download_url = 'http://code.google.com/p/rssdler/downloads/list',
    license = 'GPLv2',
    platforms = ['Posix', 'Windows', 'OSX'],
    scripts = ('rssdler',),
    py_modules = ['rssdler',],
    cmdclass = {'build_scripts': build_scripts_rename,    },
)
