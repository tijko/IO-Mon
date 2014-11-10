#!/usr/bin/env python

import os
import sys

from gi.repository import GObject
from lib.io_object import IoMonitor


class InitIoMon(object):

    def __init__(self, iomonitor_obj):
        self.iomonitor_obj = iomonitor_obj
    
    def run(self):
        self.daemonize()
        GObject.MainLoop().run()
    
    def _fork(self):
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError:
            sys.exit(1)

    def daemonize(self):
        self.iomonitor_obj()
        self._fork()
        os.chdir('/')
        os.setsid()
        os.umask(0)
        self._fork()
        return



if __name__ == '__main__':
    iomon = InitIoMon(IoMonitor)
    iomon.run()
