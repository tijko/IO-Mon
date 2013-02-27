IO/Mon
====

I/O monitoring with netlink sockets and made available as a dbus service.

You can invoke the script manually or set it up to be called on startup.

There is the use of the psutil  module that isn't part of python's standard lib.
For psutil you can either, 

    pip-install psutil

Or grab a copy from source @http://code.google.com/p/psutil/.

Since IO-Mon is a service on the system-bus you will need to put the
org.iomonitor.conf file in your dbus/system.d/ directory.





