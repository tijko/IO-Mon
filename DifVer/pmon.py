#!/usr/bin/env python

import os
import dbus
import daemon
import psutil
import gobject
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

"""

 Running as a daemon, keeping stats on every process run --> disk.write/ disk.read/ swap/ memory/
 
 Keep the actually names of the process(pids are dynamic?) when ever above happens compound list 

 data.  

"""


class IoMonitor(dbus.service.Object):
    
    def __init__(self):
        name = dbus.service.BusName('org.iomonitor', dbus.SystemBus(mainloop=DBusGMainLoop()))
        dbus.service.Object.__init__(self, name, '/org/iomonitor')
        # this below may not be needed but, keep for now 
        # because of the dictionary mappings 
        self.data = {}
        self.namepid = {}
        self.proc_name = []
        self.pids = [i for i in os.listdir('/proc') if i.isdigit()]
        for i in self.pids:
            if os.path.isfile('/proc/%s/stat' % i):
                with open('/proc/%s/stat' % i, 'r+') as f:
                    name = f.readline()
                f.close()
                name = [j for j in name.split(' ') if '(' in j]
                self.proc_name.append(name[0][1:-1])
                self.namepid[name[0][1:-1]] = i
                with open('/proc/%s/io' % i, 'r+') as f:
                    nums = f.readlines()
                f.close()
                self.data[name[0][1:-1]] = nums

    @dbus.service.method('org.iomonitor', out_signature='s')
    def stat_object(self):
        return 'object'

    @dbus.service.method('org.iomonitor', out_signature='as')
    def process_lst(self):
        pidnamelst = []
        prclst = [pid for pid in os.listdir('/proc') if pid.isdigit()]
        for pid in prclst:
            if os.path.isfile('/proc/%s/stat' % pid):
                with open('/proc/%s/stat' % pid, 'r+') as f:
                    name = f.readline()
                f.close()
                name = [j for j in name.split(' ') if '(' in j]
                pidnamelst.append(name[0][1:-1])
        return pidnamelst

    @dbus.service.method('org.iomonitor', out_signature='aas')
    def allproc_stats(self):
        total = []
        proclst = [pid for pid in os.listdir('/proc') if pid.isdigit()]
        for pid in proclst:
            if os.path.isfile('/proc/%s/io' % pid):
                with open('/proc/%s/io' % pid, 'r+') as f:
                    total.append(f.readlines())
                f.close()
        return total

    @dbus.service.method('org.iomonitor', in_signature='i', out_signature='s')
    def process_stats(self, pid):
        if os.path.isfile('/proc/%s/io' % pid):
            with open('/proc/%s/io' % pid) as f:
                info = f.readlines()
            f.close()
            return str(info)
        else:
            return 'Not a valid Process.'

    @dbus.service.method('org.iomonitor', in_signature='i', out_signature='as')
    def proc_swp(self, pid):
        with open('/proc/swaps') as f:
            data = f.readlines()
        f.close()
        if len(data) > 1:
            return data
        return ['No swap']

    @dbus.service.method('org.iomonitor', out_signature='s')
    def memory(self):
        return str(psutil.avail_phymem())

    @dbus.service.method('org.iomonitor', out_signature='as')
    def diskinfo(self):
        return [str(i) for i in psutil.disk_partitions()]

    @dbus.service.method('org.iomonitor', out_signature='as')
    def disklst(self):
        return [str(i) for i in psutil.disk_partitions('true')]


if __name__ == '__main__':
    with daemon.DaemonContext():
        iom = IoMonitor
        iom()
        gobject.MainLoop().run()

