import os
import socket
import _thread
from thread import new_thread

from untar import untar

s = socket.socket()
s.bind(("0.0.0.0", 9000))
s.listen(1)

_thread.start_new_thread(new_thread, ())

while True:
    cl, claddr = s.accept()
    cl_file = cl.makefile("rb", 0)

    try:
        os.mkdir("deploy")
    except:
        pass

    data = cl_file.read()
    untar("deploy/", data)

    cl.send(b"OK")

    cl.close()

    _thread.exit()
