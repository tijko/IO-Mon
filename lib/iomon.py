#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import struct
import socket

import dbus
import dbus.service

from taskstats import taskstats
from dbus.mainloop.glib import DBusGMainLoop


class IoMonitor(dbus.service.Object):

    def __init__(self):
        name = dbus.service.BusName('org.iomonitor', dbus.SystemBus(
                                                     mainloop=DBusGMainLoop()))
        super(IoMonitor, self).__init__(name, '/org/iomonitor')
        self.pid = os.getpid()
        self.tasks = Taskstats(self.pid)

    @dbus.service.method('org.iomonitor', out_signature='as')
    def process_list(self):
        pidnames = list() 
        for pid in os.listdir('/proc'):
            if pid.isdigit() and os.path.isfile('/proc/%s/comm' % pid):
                with open('/proc/%s/comm' % pid, 'r') as f:
                    pidnames.append(f.readline().strip('\n'))
        return pidnames

    @dbus.service.method('org.iomonitor', out_signature='as')
    def all_proc_stats(self):
        #XXX set up netlink connection for read and write stats
        #    run through a pid - list and map the names to the
        #    read/write
        write = self.tasks.write()
        read = self.tasks.read()
        return {v:k for k,v in all_proc_stat.items()}

    @dbus.service.method('org.iomonitor', in_signature='s', out_signature='s')
    def single_proc_stats(self, pid=None):
        #XXX set up netlink connection for read and write stats
        if pid is None:
            return 'Error: must a process number'
        all_proc_stat = self.gentlnk_taskstat()
        if all_proc_stat.get(pid):
            return all_proc_stat[pid]
        return 'No i/o for %s' % pid

    @dbus.service.method('org.iomonitor', out_signature='as')
    def process_swap(self):
        with open('/proc/swaps') as f:
            data = f.readlines()
        if len(data) > 1:
            return data
        return ['No swap']

    @dbus.service.method('org.iomonitor', out_signature='s')
    def memory(self):
        data_size = {'kB':1024, 'mB':2048, 'gB':4096}
        with open('/proc/meminfo') as f:
            memory = f.read()
        memory = memory.split()[1:6]
        total_mem = int(memory[0]) * data_size[memory[1]]
        free_mem = int(memory[3]) * data_size[memory[4]]
        used_mem = total_mem - free_mem 
        return "Used Memory %s | Free Memory %s" % (used_mem, free_mem)

    @dbus.service.method('org.iomonitor', in_signature='s', out_signature='as')
    def diskstats(self, disk=None):
        if disk is None:
            return ['Provide a device']
        with open('/sys/block/sda/%s/stat' % disk) as f:
            stats= f.read()
        disk_stats = disk_stats.split()
        return ['read %s write %s' % (disk_stats[0], data[4])]

    @dbus.service.method('org.iomonitor', out_signature='as')
    def disklist(self):
        dl = os.listdir('/sys/block')
        return dl

    @dbus.service.method('org.iomonitor', out_signature='as')
    def deviceinfo(self):
        with open('/proc/scsi/scsi', 'r') as f:
            devinfo = f.readlines()
        return devinfo

