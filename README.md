IO/Mon
====

#### About

I/O monitoring with netlink sockets and made available as a dbus service.

You can invoke the script manually or set it up to be called on startup.

#### Configuration

Since IO-Mon is a service on the system-bus you will need to put the 
`org.iomonitor.conf` file in your `/etc/dbus-1/session.d/` directory to provide 
the proper security credentials.
