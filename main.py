import os
import socket
import _thread
import machine
import network

import secrets

# functions
def wifi_connect():
    """Connect to WiFi AP"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        try:
            if secrets.WIFI_IFCONFIG:
                wlan.ifconfig(secrets.WIFI_IFCONFIG)
        except:
            pass
        wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
        while not wlan.isconnected():
            pass
        print(wlan.ifconfig())

def start_deployed():
    """Start deployed script"""
    try:
        os.chdir("deploy")
        with open("__init__.py", "r") as f:
            exec(f.read())
    except Exception as e:
        print("Start deployed script failed: ", e)

def untar(prefix: str, data):
    """Untar bytes"""
    def get_filename(remain_data) -> str:
        return remain_data[:100].decode().replace("\x00", "")
    def write_file(filename, remain_data) -> int:
        size = int(data[124:135].decode(), 8)
        file_end = 512 + size
        with open(filename, "wb") as f:
            f.write(remain_data[512:file_end])
        return (file_end // 512 + 1) * 512
    def is_eoa(remain_data):
        if len(remain_data) < 1024:
            return True
        for i in range(1024):
            if remain_data[i] != 0:
                return False
        return True

    def mkdir_filename(filename: str):
        if "/" not in filename:
            return
        path_list = filename.split("/")[:-1]
        for i in range(1, len(path_list) + 1):
            try:
                os.mkdir("/".join(path_list[:i]))
            except:
                pass

    next_block = 0
    while True:
        remain_data = data[next_block:]
        filename = prefix + get_filename(remain_data)
        mkdir_filename(filename)
        next_block += write_file(filename, remain_data)
        if is_eoa(data[next_block:]):
            break

def start_server():
    """Start TCP server"""
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

def server_loop():
    while True:
        try:
            start_server()
        except Exception as e:
            print(e)


# main
wifi_connect()
_thread.start_new_thread(server_loop, ())
start_deployed()
