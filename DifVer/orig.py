#!/usr/bin/env python

import optparse
import os
import threading
import daemon
import psutil 

import glib
import dbus
import gobject
import dbus.service
from dbus.mainloop.glib import threads_init
from dbus.mainloop.glib import DBusGMainLoop

import iotop
import iotop.data
from iotop import ui
from iotop.ui import find_uids
from iotop.data import Stats
from iotop.data import ProcessInfo
from iotop.data import ProcessList
from iotop.data import TaskStatsNetlink


def optpar():
    parser = optparse.OptionParser()
    parser.add_option('-a', '--accumulated', action='store_true', 
                        dest='accumulated', default=True)
    parser.add_option('-o', '--only', action='store_true', 
                        dest='only', default=False)
    parser.add_option('-b', '--batch', action='store_true', 
                        dest='batch', default=True)
    parser.add_option('-k', '--kilobytes', action='store_true',
                        dest='kilobytes', default=False)
    parser.add_option('-p', '--pids', type='int', dest='pids',
                        action='append', metavar='PID')
    parser.add_option('-n', '--iter', type='int', 
                        dest='iterations', metavar='NUM')
    parser.add_option('-t', '--time', action='store_true', dest='time')
    parser.add_option('-q', '--quiet', action='count', dest='quiet', default=0)
    parser.add_option('-d', '--delay', type='float', dest='delay_seconds',
                        metavar='SEC', default=1)
    options, args = parser.parse_args()
    return options

options = optpar()
options.processes = None
options.uids = []
options.pids = []


class WarningIndicator(dbus.service.Object):

    def __init__(self, options):
        name = dbus.service.BusName('org.ProcessIndicator', dbus.SessionBus(mainloop=DBusGMainLoop()))
        dbus.service.Object.__init__(self, name, '/org/ProcessIndicator')
        self.processes = [int(i) for i in os.listdir('/proc') if i.isdigit()]
        self.options = options
        self.tsk_stats = TaskStatsNetlink(options)
        self.proc_lst = ProcessList(self.tsk_stats, options)
        self.total = self.proc_lst.refresh_processes()
        self.total_read, self.total_write = self.total
        self.info = ui.IOTopUI(None, self.proc_lst, options).get_data()
        self.info = [i.split() for i in self.info]

    @dbus.service.method('org.ProcessIndicator', out_signature='s')
    def stat_object(self): 
        return str(ui.IOTopUI(None, self.proc_lst, self.options)) 

    @dbus.service.method('org.ProcessIndicator', out_signature='as')
    def process_objs(self):
        return [str(ProcessInfo(i)) for i in self.processes]

    @dbus.service.method('org.ProcessIndicator', out_signature='aas')
    def allproc_stats(self):
        return [i[:3] + [''.join(i[n:n+2]) for n in xrange(3,11,2)] + i[11:] for i in self.info]

    @dbus.service.method('org.ProcessIndicator', in_signature='i', out_signature='as')
    def process_stats(self, pid):
        return ui.format_stats(options, ProcessInfo(pid), 1)
#        self.info = ui.IOTopUI(None, self.proc_lst, options).get_data()
#        self.info = [i.split() for i in self.info]
#        for p in self.info:
#            if int(p[0]) == pid:
#                return p[:3] + [''.join(p[n:n+2]) for n in xrange(3,11,2)] + p[11:]

    @dbus.service.method('org.ProcessIndicator', in_signature='i', out_signature='s')
    def proc_swap(self, pid):
        for p in self.info:
            if int(p[0]) == pid:
                return p[7] + p[8] 

    @dbus.service.method('org.ProcessIndicator', out_signature='s')
    def memory(self):
        return str(psutil.avail_phymem())

    @dbus.service.method('org.ProcessIndicator', out_signature='as')
    def disklst(self):
        return [str(i) for i in psutil.disk_partitions()] 

    @dbus.service.method('org.ProcessIndicator', in_signature='s', out_signature='as')
    def diskinfo(self, diskid):
        return [str(i) for i in psutil.disk_partitions(diskid)]


if __name__ == '__main__':
    with daemon.DaemonContext():
        wi = WarningIndicator
        wi(options)
        gobject.threads_init()
        dbus.mainloop.glib.threads_init()
        d_main_loop = gobject.MainLoop()
        d_loop_thread = threading.Thread(name='glib_mainloop', target=d_main_loop.run)
        d_loop_thread.start()
        uithread = threading.Thread(target=ui.run_iotop(options))
        uithread.start()                
#        gobject.MainLoop().run()
