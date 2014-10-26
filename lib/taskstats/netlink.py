#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct
import os


# Flag values
NLM_F_REQUEST   = 1
NLM_F_MULTI     = 2
NLM_F_ACK       = 4
NLM_F_ECHO      = 8
NLM_F_DUMP_INTR = 16

# Modifiers to GET request
NLM_F_ROOT   = 0x100
NLM_F_MATCH  = 0x200
NLM_F_ATOMIC = 0x400
NLM_F_DUMP   = (NLM_F_ROOT | NLM_F_MATCH)

# Modifiers to NEW requests
NLM_F_REPLACE   = 0x100
NLM_F_EXCL      = 0x200
NLM_F_CREATE    = 0x400
NLM_F_APPEND    = 0x800

NLMSG_ALIGNTO   = 4

NLMSG_MIN_TYPE  = 0x10
NLMSG_ERROR     = 0x2

GENL_ID_CTRL = NLMSG_MIN_TYPE

NLMSG_HDRLEN = struct.calcsize('IHHII')
GENL_HDRLEN  = struct.calcsize('BBxx')


class Nlmsg(dict):
    '''
    The Nlmsg container class handles the assembly of netlink headers and
    encapsulation of the associated fields.

    struct nlmsghdr {
        __u32 nlmsg_len;
        __u16 nlmsg_type;
        __u16 nlmsg_flags;
        __u32 nlmsg_seq;
        __u32 nlmsg_pid;
    };

    Nlmsg subclasses `dict` type where the associated key-value pairs are the
    struct-fields of the netlink message header. The `.pack()` method returns a
    binary c-formatted string of the complete netlink message, header and 
    payload.

    @param nlmsg_type :: the netlink message type
    @type  nlmsg_type :: int

    @param genlmsg :: a Genlmsg object which will be the message payload
    @type  genlmsg :: Genlmsg Class Object.
    '''
    def __init__(self, nlmsg_type, pid, genlmsg):
        super(Nlmsg, self).__init__()
        self.fields = ['nl_len', 'nl_type', 'nl_flags', 'nl_seq', 'nl_pid']
        self['nl_pid'] = pid
        self['nl_flags'] = NLM_F_REQUEST
        self['nl_len'] = NLMSG_HDRLEN
        self['nl_type'] = nlmsg_type
        self['nl_seq'] = 0
        self.genlmsg = genlmsg

    def pack(self):
        payload = self.genlmsg.pack()
        self['nl_len'] += self.genlmsg.genlen
        nlmsghdr = struct.pack('IHHII', *[self[field] for field in self.fields])
        return nlmsghdr + payload


CTRL_ATTR_UNSPEC       = 0
CTRL_ATTR_FAMILY_ID    = 1
CTRL_ATTR_FAMILY_NAME  = 2
CTRL_ATTR_VERSION      = 3
CTRL_ATTR_HDRSIZE      = 4
CTRL_ATTR_MAXATTR      = 5
CTRL_ATTR_OPS          = 6
CTRL_ATTR_MCAST_GROUPS = 7
__CTRL_ATTR_MAX        = 8

CTRL_ATTR_OP_UNSPEC   = 0
CTRL_ATTR_OP_ID       = 1
CTRL_ATTR_OP_FLAGS    = 2
__CTRL_ATTR_OP_MAX    = 3

TASKSTATS_TYPE_STATS    = 3
TASKSTATS_TYPE_AGGR_PID = 4
NLA_HDRLEN = struct.calcsize('HH')
NLA_MAXPAYLOAD = 16


class Nlattr(object):
    '''
    The Nlattr is a container class that handles the assembly of
    netlink-attributes headers and enapsulation of the associated fields.

    struct nlattr {
        __u16 nla_len;
        __u16 nla_type;
    };

    The `.pack()` method returns a binary c-formattd string of the netlink
    messages attributes and the attributes data.

    The `.payload` property returns a binary c-formatted string of the Nlattr's
    payload which as far as this netlink session is concerned is either a type
    `int` or a type `str`.

    @param nla_type :: the attribute type
    @type  nla_type :: int

    @param nla_data :: the attribute payload being sent
    @type  nla_type :: int or str
    '''
    def __init__(self, nla_type, nla_data):
        self.nla_type = nla_type
        self.nla_data = nla_data
        self.nla_len = NLA_HDRLEN
        
    def pack(self):
        nla_payload = self.payload
        nla_hdr = struct.pack('HH', self.nla_len, self.nla_type)
        return nla_hdr + nla_payload

    @property
    def payload(self):
        load = ''
        if isinstance(self.nla_data, str):
            padding = calc_alignment(len(self.nla_data))
            self.nla_len += padding
            load = struct.pack('%ds' % padding, self.nla_data)
        elif isinstance(self.nla_data, int):
            self.nla_len += calc_alignment(struct.calcsize('I'))
            load = struct.pack('I', self.nla_data)
        return load


def calc_alignment(data):
    return ((data + NLMSG_ALIGNTO - 1) & ~(NLMSG_ALIGNTO - 1))

def parse_response(nlobj, reply):
    nl_len, nl_type = struct.unpack('IHHII', reply[:NLMSG_HDRLEN])[:2]
    nlattrs = reply[NLMSG_HDRLEN + GENL_HDRLEN:]
    while (nlattrs):
        nla_len, nla_type = map(int, struct.unpack('HH', nlattrs[:NLA_HDRLEN]))
        nla_len = calc_alignment(len(nlattrs[:nla_len]))
        nla_data = nlattrs[NLA_HDRLEN:nla_len]
        nlobj.attrs[nla_type] = nla_data
        nlattrs = nlattrs[nla_len:]
    return

