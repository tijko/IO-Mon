import socket
import struct
import os

def parse_attributes(data):
    attrs = {}
    while len(data):
        attr_len, attr_type = struct.unpack("HH", data[:4])
        attrs[attr_type] = Attr(attr_type, data[4:attr_len])
        attr_len = ((attr_len + 4 - 1) & ~3 )
        data = data[attr_len:]
    return attrs

class Attr:
    def __init__(self, attr_type, data, *values):
        self.type = attr_type
        if len(values):
            self.data = struct.pack(data, *values)
        else:
            self.data = data
    def nested(self):
        return parse_attributes(self.data)

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
    pad = ((length + 4 - 1) & ~3) - length
    back = back_hdr + back + b'\0' * pad
    content.append(front)
    content.append(back) 
    load = b''.join(content)
    length = len(load)
    hdr = struct.pack('IHHII', length + 4*4, 23, 1, 1, pid)
    c.send(hdr+load)
    t, (x,y) = c.recvfrom(16384)
    t = parse_attributes(t[20:])
    n = t[4].nested()[3].data
    print 'Process %d: --> Read: %d --> Write: %d' % (i, struct.unpack('Q', n[248:256])[0], struct.unpack('Q', n[256:264])[0])
