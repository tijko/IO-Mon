#!/usr/bin/env python

import os
import sys

from lib.iomon import *
from gi.repository import GObject


def fork_process():
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        sys.exit(1)
    return

def daemonize():
    fork_process()

    os.chdir('/')
    os.setsid()
    os.umask(0)

    fork_process()

    return

def main():
    daemonize()
    IoMonitor()
    GObject.MainLoop().run()


if __name__ == '__main__':
    main()
