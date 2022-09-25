import os
import socket
import _thread

from endpoints import endpoints

addr = socket.getaddrinfo("0.0.0.0", 9000)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

while True:
    cl, claddr = s.accept()
    cl_file = cl.makefile("rb", 0)

    first_line = cl_file.readline().strip()
    first_line_sp = first_line.split(b" ")
    method = first_line_sp[0].decode()
    path_query = first_line_sp[1].split(b"?")
    path = path_query[0].decode()

    headers = []
    while True:
        line = cl_file.readline().strip()
        if not line or len(line) == 0:
            break
        else:
            headers.append(line)

    body = cl_file.read()

    try:
        status, payload = endpoints[method][path](headers, body)
        cl.send(("HTTP/1.1 " + status + "\r\n").encode())
        cl.send(b"Content-Type: application/json\r\n\r\n")
        cl.send(payload.encode())
    except KeyError:
        cl.send(("HTTP/1.1 404 Not Found\r\n").encode())
        cl.send(b"Content-Type: application/json\r\n\r\n")
        cl.send(b'{"message":"NotFound"}')

    cl.shutdown(socket.SHUT_RDWR)
    cl.close()
