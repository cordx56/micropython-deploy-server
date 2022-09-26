import os
import socket
import machine

from untar import untar

def start_server():
    s = socket.socket()
    s.bind(("0.0.0.0", 9000))
    s.listen()

    cl, claddr = s.accept()
    print("Connect: ", claddr)

    data = b""
    while True:
        recv = cl.recv(1024)
        if not recv:
            break
        data += recv

    try:
        os.chdir("..")
        os.rmdir("deploy")
        os.mkdir("deploy")
    except:
        pass
    untar("deploy/", data)
    print("deployed to", os.getcwd() + "/deploy")

    cl.send(b"OK")
    cl.close()

    machine.reset()
