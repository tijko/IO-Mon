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
    @dbus.service.method('org.iomonitor', out_signature='a{si}')
    def process_list(self):
        processes = dict() 
        for pid in self.procs():
            name = self.tasks.process_name(pid)
            processes[name] = pid
        return processes

    @dbus.service.method('org.iomonitor', out_signature='aa{sa{si}}')
    def all_proc_io(self):
        all_stats = list()
        for process in self.process_list:
            write = self.tasks.write(processes[process])
            read = self.tasks.read(processes[process])
            all_stats.append({process:{'read':read, 'write':write}})
        return all_stats 

    @dbus.service.method('org.iomonitor', in_signature='i', out_signature='a{ia{si}}')
    def single_proc_io(self, pid=None):
        if pid is None:
            return 'Error: must provide a process number'
        write = self.tasks.write(pid)
        read = self.tasks.read(pid)
        return {pid:{'read':read, 'write':write}}

    @dbus.service.method('org.iomonitor', out_signature='a{si}')
    def all_proc_swap(self):
        all_swap = dict()
        for process, pid in self.process_list.items():
            all_swap[process] = self.tasks.swap(pid)
        return all_swap
        
    @dbus.service.method('org.iomonitor', in_signature='i', out_signature='a{ii}')
    def single_proc_swap(self, pid=None):
        if pid is None:
            return 'Error: must provide a process number'
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

