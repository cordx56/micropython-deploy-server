#!/usr/bin/env python3

import os
import sys
import tarfile
import socket

with tarfile.open("deploy.tar", mode="w", format=tarfile.USTAR_FORMAT) as f:
    os.chdir("deploy")
    for file in os.listdir():
        f.add(file)
os.chdir("..")

host = sys.argv[1]
with open("deploy.tar", "rb") as f:
    data = f.read()
os.remove("deploy.tar")

with socket.socket() as s:
    s.connect((host, 9000))
    s.send(data)
    s.close()
