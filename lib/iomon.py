import os
import struct
import socket
import collections

import psutil # maybe not..

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

"""

Make the methods polling /sys/block/dev/... for device i/o

"""


class IoMonitor(dbus.service.Object):

    def __init__(self):
        name = dbus.service.BusName('org.iomonitor', dbus.SystemBus(mainloop=DBusGMainLoop()))
        super(IoMonitor, self).__init__(name, '/org/iomonitor')
        self.conn = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, 16)
        self.conn.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        self.conn.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        self.conn.bind((0,0))
        self.pid, self.grp = self.conn.getsockname()

    def netlink_data(self):
        aps = collections.defaultdict(int)
        ps = [int(i) for i in os.listdir('/proc') if i.isdigit()]
        for pid in ps:
            front = struct.pack('HH', 1, 0)
            back = struct.pack('I', pid)
            back_hdr = struct.pack('HH', len(back) + 4, 1)
            back = back_hdr + back
            load = b''.join(front+back)
            hdr = struct.pack('IHHII', len(load) + 16, 23, 1, 1, self.pid)
            self.conn.send(hdr+load)
            t, (x, y) = self.conn.recvfrom(16384)
            t = t[20:]
            a = {}
            while 3 not in a.keys():
                while len(t):
                    atl, aty = struct.unpack('HH', t[:4])
                    a[aty] = t[4:atl]
                    t = t[atl:]
                t = a[aty]
            try:
                aps['PID: ' + str(pid) + ' READ: ' + 
                    str(struct.unpack('Q', t[248:256])[0]) + 
                    ' WRITE: ' + str(struct.unpack('Q', t[256:264])[0])] += 1  
            except struct.error:
                pass
        return aps

    @dbus.service.method('org.iomonitor', out_signature='as')
    def process_list(self):
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

    @dbus.service.method('org.iomonitor', out_signature='as')
    def all_proc_stats(self):
        aps = self.netlink_data()
        return aps

    @dbus.service.method('org.iomonitor', in_signature='s', out_signature='s')
    def single_proc_stats(self, pid):
        aps = self.netlink_data()
        for i in aps:
            chk = i.split(' ')
            if pid == chk[1]:
                return i
        return ['No i/o']

    @dbus.service.method('org.iomonitor', out_signature='as')
    def process_swap(self):
        # check if this best place to monitor?
        with open('/proc/swaps') as f:
            data = f.readlines()
        f.close()
        if len(data) > 1:
            return data
        return ['No swap']

    @dbus.service.method('org.iomonitor', out_signature='s')
    def memory(self):
        # work out psutil
        return str(psutil.avail_phymem())

    @dbus.service.method('org.iomonitor', in_signature='s', out_signature='as')
    def diskstats(self, disk):
        with open('/sys/block/sda/%s/stat' % disk, 'r') as f:
            data = f.readlines()
        f.close()
        data = [i for i in data[0].split(' ') if len(i) > 0]
        return ['read ' + data[0], 'write ' + data[4]]

    @dbus.service.method('org.iomonitor', out_signature='as')
    def disklist(self):
        # /sys/block/dev/...just sda/hda -- or all partitions??
        dl = os.listdir('/sys/block')
        return dl
    @dbus.service.method('org.iomonitor', out_signature='as')
    def deviceinfo(self):
        with open('/proc/scsi/scsi', 'r') as f:
            devinfo = f.readlines()
        f.close()
        return devinfo

