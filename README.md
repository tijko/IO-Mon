IO/Mon
====

I/O monitoring with netlink sockets and made available as a dbus service.

You can invoke the script manually or set it up to be called on startup.


Since IO-Mon is a service on the system-bus you will need to put the 
`org.iomonitor.conf` file in your `/etc/dbus-1/system.d/` directory to provide 
the proper security credentials.

