#!/usr/bin/env python

import os
import sys

import gobject

from lib.iomon import *

def daemonize():
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        sys.exit(1)

    os.chdir('/')
    os.setsid()
    os.umask(0)

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        sys.exit(1)

    return

def main():
    daemonize()
    iom = IoMonitor
    iom()
    gobject.MainLoop().run()


if __name__ == '__main__':
    main()
