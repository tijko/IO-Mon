import socket
import struct
import os

def trial(attr_type, data, *values):
    if len(values):
        data = struct.pack(data, *values)
        return data
    else:
        return data

def test(t):
    a = {}
    while 3 not in a.keys():
        while len(t):
            atl, aty = struct.unpack('HH', t[:4])
            print len(t[4:atl]), atl
            a[aty] = trial(aty, t[4:atl])
            atl = ((atl + 3) & ~3)
            t = t[atl:]
        t = a[4]
    return a[3]

ps = [int(i) for i in os.listdir('/proc') if i.isdigit()]
c = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, 16)
c.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
c.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
c.bind((0,0))
pid, grp = c.getsockname() 
for i in ps:
    content = []
    front = struct.pack('BBxx', 1, 0) 
    back = struct.pack('I', i) 
    back_hdr = struct.pack('HH', len(back) + 4, 1)
    length = len(back)
    pad = ((length + 3) & ~3) - length
    back = back_hdr + back + b'\0' * pad
    content.append(front)
    content.append(back) 
    load = b''.join(content)
    length = len(load)
    hdr = struct.pack('IHHII', length + 16, 23, 1, 1, pid)
    c.send(hdr+load)
    t, (x,y) = c.recvfrom(16384)
    t = test(t[20:])
    n = t[:]
    print 'Process %d: --> Read: %d --> Write: %d' % (i, struct.unpack('Q', n[248:256])[0], struct.unpack('Q', n[256:264])[0])
