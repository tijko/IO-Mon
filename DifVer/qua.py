import socket
import struct
import os

def test(t):
    a = {}
    while 3 not in a.keys():
        while len(t):
            atl, aty = struct.unpack('HH', t[:4])
            a[aty] = t[4:atl]
            t = t[atl:]
        t = a[4]
    return a[3]

ps = [int(i) for i in os.listdir('/proc') if i.isdigit()]
conn = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, 16)
conn.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
conn.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
conn.bind((0,0))
pid, grp = conn.getsockname() 
for i in ps:
    front = struct.pack('BBxx', 1, 0) 
    back = struct.pack('I', i) 
    back_hdr = struct.pack('HH', len(back) + 4, 1)
    back = back_hdr + back 
    load = b''.join(front+back)
    hdr = struct.pack('IHHII', len(load) + 16, 23, 1, 1, pid)
    conn.send(hdr+load)
    t, (x,y) = conn.recvfrom(16384)
    t = test(t[20:])
    print 'Process %d: --> Read: %d --> Write: %d' % (i, struct.unpack('Q', t[248:256])[0], struct.unpack('Q', t[256:264])[0])
