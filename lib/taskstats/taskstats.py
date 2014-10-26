#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
This module sets a netlink connection, which will be used to communicate
the taskstats data.
'''

import struct

from netlink import *
from controller import Controller, Genlmsg


# Taskstats commands
TASKSTATS_CMD_UNSPEC = 0
TASKSTATS_CMD_GET    = 1
TASKSTATS_CMD_NEW    = 2
_TASKSTATS_CMD_MAX   = 3

# Taskstats response types
TASKSTATS_TYPE_UNSPEC    = 0
TASKSTATS_TYPE_PID       = 1
TASKSTATS_TYPE_TGID      = 2
TASKSTATS_TYPE_STATS     = 3
TASKSTATS_TYPE_AGGR_PID  = 4
TASKSTATS_TYPE_AGGR_TGID = 5
TASKSTATS_TYPE_NULL      = 7
__TASKSTATS_TYPE_MAX     = 6

# Taskstats command attributes
TASKSTATS_CMD_ATTR_UNSPEC             = 0
TASKSTATS_CMD_ATTR_PID                = 1
TASKSTATS_CMD_ATTR_TGID               = 2
TASKSTATS_CMD_ATTR_REGISTER_CPUMASK   = 3
TASKSTATS_CMD_ATTR_DEREGISTER_CPUMASK = 4
__TASKSTATS_CMD_ATTR_MAX              = 5

TASKSTATS_GENL_NAME = 'TASKSTATS'

taskstat_struct = (('version', 'H'), ('ac_exitcode', 'I'), ('ac_flag', 'B'),
                   ('ac_nice', 'B'), ('align', 'I'), ('cpu_count', 'Q'),
                   ('cpu_delay_total', 'Q'), ('blkio_count', 'Q'),
                   ('blkio_delay_total', 'Q'), ('swapin_count', 'Q'),
                   ('swapin_delay_total', 'Q'), ('cpu_run_real_total', 'Q'),
                   ('cpu_run_virtual_total', 'Q'), ('ac_comm', '32s'),
                   ('ac_sched', 'B'), ('ac_pid', '3x'), ('align', 'BB'),
                   ('ac_uid', 'I'), ('ac_gid', 'I'), ('ac_pid', 'I'),
                   ('ac_ppid', 'I'), ('ac_btime', 'I'), ('align', 'B'),
                   ('ac_etime', 'Q'), ('ac_utime', 'Q'), ('ac_stime', 'Q'),
                   ('ac_minflt', 'Q'), ('ac_majflt', 'Q'), ('coremem', 'Q'),
                   ('virtmem', 'Q'), ('hiwater_rss', 'Q'), ('hiwater_vm', 'Q'),
                   ('read_char', 'Q'), ('write_char', 'Q'),
                   ('read_syscalls', 'Q'), ('write_syscalls', 'Q'),
                   ('read_bytes', 'Q'), ('write_bytes', 'Q'),
                   ('cancelled_write_bytes', 'Q'), ('nvcsw', 'Q'),
                   ('nivcsw', 'Q'), ('ac_utimescaled', 'Q'),
                   ('ac_stimescaled', 'Q'), ('cpu_scaled_run_real_total', 'Q'),
                   ('freepages_count', 'Q'), ('freepages_delay_total', 'Q'))


class Taskstats(object):
    '''
    The Taskstats class makes requests to assemble netlink messages that
    communicate taskstats.
    '''
    def __init__(self, pid):
        super(Taskstats, self).__init__()
        self.pid = pid
        self.genlctrl = Controller(TASKSTATS_GENL_NAME)
        self.attrs = dict()
        self.taskstats_fields = [task[0] for task in taskstat_struct]
        self.fmt = ''.join([task[1] for task in taskstat_struct])

    def get_task(self, task, pid):
        task_msg_payload = Genlmsg(TASKSTATS_CMD_GET, Nlattr(
                                   TASKSTATS_CMD_ATTR_PID, pid))
        self.genlctrl.send(Nlmsg(self.genlctrl.fam_id, self.pid, 
                                         task_msg_payload).pack())
        task_response = self.genlctrl.recv()
        parse_response(self, task_response[NLA_HDRLEN:])
        taskstats_raw = self.attrs[TASKSTATS_TYPE_STATS]
        taskstats = dict(zip(self.taskstats_fields,
                             struct.unpack(self.fmt, taskstats_raw)))
        return taskstats.get(task)
                            
    def read(self, pid):
        taskstats_read = self.get_task('read_bytes', pid)
        return taskstats_read

    def write(self, pid):
        taskstats_write = self.get_task('write_bytes', pid)
        return taskstats_write
