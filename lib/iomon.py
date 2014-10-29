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

    @dbus.service.method('org.iomonitor', out_signature='a{si}')
    def process_list(self):
        processes = dict() 
        for pid in self.procs():
            name = self.tasks.process_name(pid)
            processes[name] = pid
        return processes

    @dbus.service.method('org.iomonitor', out_signature='aa{sa{si}}')
    def all_proc_stats(self):
        processes = self.process_list()
        all_stats = list()
        for process in processes:
            write = self.tasks.write(processes[process])
            read = self.tasks.read(processes[process])
            all_stats.append({process:{'read':read, 'write':write}})
        return all_stats 

    @dbus.service.method('org.iomonitor', in_signature='i', out_signature='a{ia{si}}')
    def single_proc_stats(self, pid=None):
        if pid is None:
            return 'Error: must provide a process number'
        write = self.tasks.write(pid)
        read = self.tasks.read(pid)
        return {pid:{'read':read, 'write':write}}

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

