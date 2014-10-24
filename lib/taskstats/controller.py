#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct
import socket

from netlink import *


NETLINK_ROUTE           = 0
NETLINK_UNUSED          = 1
NETLINK_USERSOCK        = 2
NETLINK_FIREWALL        = 3
NETLINK_SOCK_DIAG       = 4
NETLINK_NFLOG           = 5
NETLINK_XFRM            = 6
NETLINK_SELINUX         = 7
NETLINK_ISCSI           = 8
NETLINK_AUDIT           = 9
NETLINK_FIB_LOOKUP      = 10
NETLINK_CONNECTOR       = 11
NETLINK_NETFILTER       = 12
NETLINK_IP6_FW          = 13
NETLINK_DNRTMSG         = 14
NETLINK_KOBJECT_UEVENT  = 15
NETLINK_GENERIC         = 16
NETLINK_SCSITRANSPORT   = 18
NETLINK_ECRYPTFS        = 19
NETLINK_RDMA            = 20
NETLINK_CRYPTO          = 21
NETLINK_INET_DIAG = NETLINK_SOCK_DIAG


class Connection(object):
    '''
    Base class that establishes a netlink connection with the kernel.
    '''
    def __init__(self, family):
        self.family = family
        self.conn = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, family)
        self.conn.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        self.conn.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        self.conn.bind((0, 0))

    def send(self, msg):
        self.conn.send(msg)

    def recv(self):
        return self.conn.recv(65536)

# Genetlink Controller command and attribute values
CTRL_CMD_UNSPEC         = 0
CTRL_CMD_NEWFAMILY      = 1
CTRL_CMD_DELFAMILY      = 2
CTRL_CMD_GETFAMILY      = 3
CTRL_CMD_NEWOPS         = 4
CTRL_CMD_DELOPS         = 5
CTRL_CMD_GETOPS         = 6
CTRL_CMD_NEWMCAST_GRP   = 7
CTRL_CMD_DELCAST_GRP    = 8
CTRL_CMD_GETMCAST_GRP   = 9
__CTRL_CMD_MAX          = 10

TASKSTATS_GENL_VERSION = 0x1

GENL_HDRLEN = struct.calcsize('BBxx')


class Genlmsg(object):
    '''
    Generic netlink message container, this class is to encapsulate the fields
    of struct genlmsghdr.

    struct genlmsghdr {
        __u8 cmd;
        __u8 version;
        __u16 reserved;
    };

    the `.pack()` method returns a binary c-formatted string of the generic
    netlink header and its associated payload.

    @param cmd :: the generic netlink command.
    @type  cmd :: int

    @param nlattr :: Nlattr object containing the attributes for the call.
    @type  nlattr :: Nlattr Class Object

    @param version :: the generic netlink version of the interface (defaults to 
                      taskstats)
    @type  version :: int
    '''
    def __init__(self, cmd, nlattr, version=TASKSTATS_GENL_VERSION):
        self.cmd = cmd
        self.version = version
        self.nlattr = nlattr
        self.payload = self.nlattr.pack()
        self.genlen = GENL_HDRLEN + self.nlattr.nla_len

    def pack(self):
        genlhdr = struct.pack('BBxx', self.cmd, self.version)
        return genlhdr + self.payload


class Controller(Connection):
    '''
    Controller class that establishes a generic netlink connection with
    family of the supplied 'genl_name'.
    '''
    def __init__(self, genl_name):
        super(Controller, self).__init__(NETLINK_GENERIC)
        self.genl_name = genl_name
        self.genlhdr = Genlmsg(CTRL_CMD_GETFAMILY, Nlattr(CTRL_ATTR_FAMILY_NAME,
                                                                self.genl_name))
        self.attrs = dict()
        self.fam_id = self.get_family_id

    @property
    def get_family_id(self):
        nlmsg = Nlmsg(GENL_ID_CTRL, self.genlhdr).pack()
        self.send(nlmsg)
        family_id_reply = self.recv()
        parse_response(self, family_id_reply)
        return struct.unpack('I', self.attrs[CTRL_ATTR_FAMILY_ID])[0]

