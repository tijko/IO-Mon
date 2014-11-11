#!/usr/bin/env python

import os
import sys

from gi.repository import GObject
from lib.io_object import IoMonitor


class InitIoMon(object):
    '''
    Initializing class for IO-Mon that creates the main instance of IoMonitor
    (the dbus object to export).  Inside the IoMonitor instance the 
    DBusGMainLoop is called to allow GObject mainloop integration.

    After daemonizing the process, lastly the GObject mainloop is then 
    initialized and run.

    @param iomonitor_obj :: the main class representing the dbus object.
    @type  iomonitor_obj :: type <class 'dbus.service.InterfaceType'>.
    '''
    def __init__(self, iomonitor_obj):
        super(InitIoMon, self).__init__()
        self.iomonitor_obj = iomonitor_obj
        self.gobj_loop = GObject.MainLoop()
 
    def run(self):
        self.iomonitor_obj()
        self.daemonize()
        self.gobj_loop.run()
    
    def _fork(self):
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError:
            sys.exit(1)

    def daemonize(self):
        self._fork()
        os.chdir('/')
        os.setsid()
        os.umask(0)
        self._fork()
        return



if __name__ == '__main__':
    iomon = InitIoMon(IoMonitor)
    iomon.run()
