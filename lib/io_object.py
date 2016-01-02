#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import struct
import socket

import dbus
import dbus.service

from taskstats.taskstats import Taskstats
from dbus.mainloop.glib import DBusGMainLoop


class IoMonitor(dbus.service.Object):

    def __init__(self):
        name = dbus.service.BusName('org.iomonitor', dbus.SystemBus(
                                                     mainloop=DBusGMainLoop()))
        super(IoMonitor, self).__init__(name, '/org/iomonitor')
        self.pid = os.getpid()
        self.tasks = Taskstats(self.pid)
        self.is_pid = lambda file_name: file_name.isdigit()
        self.procs = lambda: map(int, filter(self.is_pid, os.listdir('/proc')))

    @property
    def process_list(self):
        pids = self.procs()
        return dict(zip(map(self.tasks.process_name, pids), pids))

    @dbus.service.method('org.iomonitor', out_signature='aa{sa{st}}')
    def all_proc_io(self):
        all_stats = list()
        for process in self.process_list:
            write = self.tasks.write(self.process_list[process])
            read = self.tasks.read(self.process_list[process])
            all_stats.append({process:{'read':read, 'write':write}})
        return all_stats 

    @dbus.service.method('org.iomonitor', in_signature='i', out_signature='a{ia{st}}')
    def single_proc_io(self, pid=None):
        if pid is None:
            raise dbus.DBusException('''Invalid arg of type <NoneType> ::  
                                                 must be of type <int>''')
        write = self.tasks.write(pid)
        read = self.tasks.read(pid)
        return {pid:{'read':read, 'write':write}}

    @dbus.service.method('org.iomonitor', out_signature='a{st}')
    def all_proc_swap(self):
        return {p:self.tasks.swap(pid) for p, pid in self.process_list.items()}
        
    @dbus.service.method('org.iomonitor', in_signature='i', out_signature='a{it}')
    def single_proc_swap(self, pid=None):
        if pid is None:
            raise dbus.DBusException('''Invalid arg of type <NoneType> :: 
                                                 must be of type <int>''')
        pid_swap = self.tasks.swap(pid)
        return {pid:pid_swap}

    @dbus.service.method('org.iomonitor', out_signature='a{si}')
    def memory(self):
        with open('/proc/meminfo') as f:
            memory = f.read()
        memory = memory.split()
        total, free = map(int, [memory[1], memory[4]])
        return {'total_mem':total, 'free_mem':free, 'used_mem':total - free}

    @dbus.service.method('org.iomonitor', in_signature='s', out_signature='as')
    def diskstats(self, disk=None):
        if disk is None:
            raise dbus.DBusException('''Invalid arg of type <NoneType> :: 
                                                 must be of type <str>''')
        with open('/sys/block/sda/%s/stat' % disk) as f:
            raw_diskstats= f.read()
        disk_stats = raw_diskstats.split()
        return ['read %s write %s' % (disk_stats[0], disk_stats[4])]

    @dbus.service.method('org.iomonitor', out_signature='as')
    def disklist(self):
        return os.listdir('/sys/block')

    @dbus.service.method('org.iomonitor', out_signature='as')
    def deviceinfo(self):
        with open('/proc/scsi/scsi', 'r') as f:
            devinfo = f.readlines()
        return devinfo

