import os
import time
import socket
import _thread
import machine
import network

import secrets

USER_INIT_FILE = "init.py"

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
        with open("init.py", "r") as f:
            exec(f.read())
    except Exception as e:
        print("Start deployed script failed: ", e)


def rm_recursive(path):
    try:
        os.rmdir(path)
    except NotADirectoryError:
        os.remove(path)
    except FileNotFoundError:
        pass
    except:
        for d in os.listdir(path):
            rm_recursive(path + "/" + d)
        os.rmdir(path)
def mkdir_filename(filename: str):
    if "/" not in filename:
        return
    path_list = filename.split("/")[:-1]
    for i in range(1, len(path_list) + 1):
        try:
            os.mkdir("/".join(path_list[:i]))
        except:
            pass
def untar(prefix: str, data):
    """Untar bytes"""
    def get_filename(remain_data) -> str:
        return remain_data[:100].decode().replace("\x00", "")
    def write_file(filename, remain_data) -> int:
        size = int(remain_data[124:135].decode(), 8)
        file_end = 512 + size
        next_block = (file_end // 512 + 1) * 512
        if size == 0:
            return next_block
        with open(filename, "wb") as f:
            f.write(remain_data[512:file_end])
        return next_block
    def is_eoa(remain_data):
        if len(remain_data) < 1024:
            return True
        for i in range(1024):
            if remain_data[i] != 0:
                return False
        return True

    next_block = 0
    remain_data = data
    while True:
        remain_data = remain_data[next_block:]
        filename = prefix + get_filename(remain_data)
        mkdir_filename(filename)
        next_block = write_file(filename, remain_data)
        if is_eoa(remain_data[next_block:]):
            break


def http_handler(data: bytes):
    def empty_callback():
        pass
    try:
        next_index = data.index(b"\r\n")
        first_line = data[:next_index]
        first_line_splitted = first_line.split(b" ")
        method = first_line_splitted[0]
        path_and_query = first_line_splitted[1]
        path = path_and_query.split(b"?")[0]
        remain_data = data[next_index + 2:]
        while True:
            next_index = remain_data.index(b"\r\n")
            line = remain_data[:next_index]
            remain_data = remain_data[next_index + 2:]
            if len(line) == 0:
                break
            elif len(remain_data) == 0:
                break
        relative_path = path.decode()[1:]

        if method == b"PUT":
            mkdir_filename(relative_path)
            with open(relative_path, "wb") as f:
                f.write(remain_data)
            return b"HTTP/1.1 201 Created", b"Created", empty_callback
        elif method == b"DELETE":
            try:
                rm_recursive(relative_path)
                return b"HTTP/1.1 200 OK", b"OK", empty_callback
            except:
                return b"HTTP/1.1 404 Not Found", b"Not Found", empty_callback
        elif method == b"GET":
            if path == b"/reset":
                def reset_callback():
                    time.sleep(1)
                    machine.reset()
                return b"HTTP/1.1 200 OK", b"OK", reset_callback
            else:
                return b"HTTP/1.1 404 Not Found", b"Not Found", empty_callback
        elif method == b"POST":
            if path == b"/tar":
                untar("", remain_data)
                return b"HTTP/1.1 201 Created", b"Created", empty_callback
            else:
                return b"HTTP/1.1 404 Not Found", b"Not Found", empty_callback
        else:
            return b"HTTP/1.1 400 Bad Request", b"Bad Request", empty_callback
    except Exception as e:
        print(e)
        return b"HTTP/1.1 500 Internal Server Error", b"Internal Server Error", empty_callback


def start_server():
    """Start TCP server"""
    s = socket.socket()
    s.bind(("0.0.0.0", 9000))
    s.listen()

    while True:
        cl, claddr = s.accept()
        print("Connect: ", claddr)

        data = b""
        while True:
            try:
                recv = cl.recv(1024)
                data += recv
                if not recv or len(recv) < 1024:
                    break
            except ConnectionResetError:
                break
        response, body, callback = http_handler(data)
        cl.send(response)
        cl.send(b"\r\n\r\n")
        cl.send(body)
        cl.close()
        callback()

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
