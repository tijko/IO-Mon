import os
import struct
import socket

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop


NLMSG_ERROR = 2
NLMSG_VERSION= 0x10
CTRL_CMD_GETFAMILY = 3
NLM_F_REQUEST = 1
CTRL_ATTR_FAMILY_ID = 1
TASKSTATS_CMD_GET = 1
TASKSTATS_CMD_ATTR_PID = 1
TASKSTATS_TYPE_AGGR_PID = 4
TASKSTATS_TYPE_STATS = 3
FAMILY_SEQ = 0
NETLINK_GENERIC = 16


class IoMonitor(dbus.service.Object):

    def __init__(self):
        name = dbus.service.BusName('org.iomonitor', dbus.SystemBus(mainloop=DBusGMainLoop()))
        super(IoMonitor, self).__init__(name, '/org/iomonitor')
        self.conn = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, 16)
        self.conn.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        self.conn.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        self.conn.bind((0,0))
        self.pid, self.grp = self.conn.getsockname()

    def build_ntlnk_payload(self, nl_type, flags):
        return struct.pack('BBxx', nl_type, flags)

    def build_ntlnk_hdr(self, version, flags, seq, pid, payload):
        length = len(payload)
        hdr = struct.pack('IHHII', length + 4*4, version, flags, seq, self.pid)
        return hdr
      
    def build_padding(self, load):
        pad = ((len(load) + 4 - 1) & ~3) - len(load)
        return pad

    def get_family_name(self):
        payload = b''.join([self.build_ntlnk_payload(CTRL_CMD_GETFAMILY, 
                                                     FAMILY_SEQ)])
        gen_id = struct.pack('%dsB' % len('TASKSTATS'), 'TASKSTATS', 0)
        pad = self.build_padding(gen_id)
        genhdr = struct.pack('HH', len(gen_id) + 4, 2)
        payload += b''.join([genhdr, gen_id, b'\0' * pad])
        hdr = self.build_ntlnk_hdr(NETLINK_GENERIC, NLM_F_REQUEST, FAMILY_SEQ + 1,
                                   self.pid, payload) 
        self.conn.send(hdr + payload)
        msg = self.conn.recvfrom(16384)[0]
        taskstat_cmd = self.parse_msg(msg[20:])[1]
        taskstat_cmd = struct.unpack('H', taskstat_cmd)[0]
        return taskstat_cmd

    def parse_msg(self, msg):
        msg_segments = {}
        while msg:
            seg_len, seg_type = struct.unpack('HH', msg[:4])
            msg_segments[seg_type] = msg[4:seg_len]
            seg_len = ((seg_len + 4 - 1) & ~3 )
            msg = msg[seg_len:]
        return msg_segments

    def gentlnk_taskstat(self):
        aps = dict()
        ps = [int(i) for i in os.listdir('/proc') if i.isdigit()]
        ntlnk_family = self.get_family_name()
        for pid in ps:
            payload = b''.join([self.build_ntlnk_payload(TASKSTATS_CMD_GET, 0)])
            gen_id = struct.pack('I', pid)
            pad = self.build_padding(gen_id)
            genhdr = struct.pack('HH', len(gen_id) + 4, 1)
            payload += b''.join([genhdr, gen_id, b'\0' * pad])
            hdr = self.build_ntlnk_hdr(ntlnk_family, NLM_F_REQUEST, FAMILY_SEQ + 2,
                                       self.pid, payload)
            self.conn.send(hdr + payload)
            msg = self.conn.recvfrom(16384)[0]
            segments = self.parse_msg(msg[20:])
            msg = self.parse_msg(segments[4])[3]
            try:
                aps[str(pid)] = ('PID: %d READ: %d WRITE %d' % 
                                (pid, struct.unpack('Q', msg[248:256])[0], 
                                 struct.unpack('Q', msg[256:264])[0]))
            except struct.error:
                aps[str(pid)] = 'ERROR'
        return aps

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
        aps = self.gentlnk_taskstat()
        return {v:k for k,v in aps.items()}

    @dbus.service.method('org.iomonitor', in_signature='s', out_signature='s')
    def single_proc_stats(self, pid=None):
        if pid is None:
            return 'Error: must a process number'
        aps = self.gentlnk_taskstat()
        if aps.get(pid):
            return aps[pid]
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
        with open('/sys/block/sda/%s/stat' % disk, 'r') as f:
            data = f.readlines()
        data = [i for i in data[0].split(' ') if len(i) > 0]
        return ['read ' + data[0], 'write ' + data[4]]

    @dbus.service.method('org.iomonitor', out_signature='as')
    def disklist(self):
        dl = os.listdir('/sys/block')
        return dl

    @dbus.service.method('org.iomonitor', out_signature='as')
    def deviceinfo(self):
        with open('/proc/scsi/scsi', 'r') as f:
            devinfo = f.readlines()
        return devinfo

