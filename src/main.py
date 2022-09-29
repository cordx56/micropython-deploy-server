"""
MIT License

Copyright (c) 2022 cordx56

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import sys
import io
import time
import socket
import _thread
import machine
import network

USER_INIT_FILE = "init.py"

def load_python_file(path):
    with open(path, "r") as f:
        script = f.read()
    exec(script)

load_python_file("secrets.py")

# functions
def wifi_connect():
    """Connect to WiFi AP"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            pass
        try:
            if WIFI_IFCONFIG:
                wlan.ifconfig(WIFI_IFCONFIG)
        except:
            pass
        print(wlan.ifconfig())

def start_deployed():
    """Start deployed script"""
    try:
        load_python_file(USER_INIT_FILE)
    except Exception as e:
        print("Start deployed script failed: ", e)
        sys.print_exception(e)

def rm_recursive(path: str):
    ENOTEMPTY = 39
    try:
        os.rmdir(path)
    except OSError as e:
        if e.errno == ENOTEMPTY:
            for d in os.listdir(path):
                rm_recursive(path + "/" + d)
            os.rmdir(path)
        else:
            sys.print_exception(e)

def cleanup(excepts=[]):
    excepts.extend(["boot.py", "main.py", "secrets.py"])
    os.chdir("/")
    for path in os.listdir():
        if path not in excepts:
            rm_recursive(path)

def mkdir_filename(filename: str):
    if "/" not in filename:
        return
    path_list = filename.split("/")[:-1]
    for i in range(1, len(path_list) + 1):
        try:
            os.mkdir("/".join(path_list[:i]))
        except:
            pass
def untar(prefix: str, data: bytes):
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


def http_handler(cl: socket.socket):
    # To prevent files from being corrupted by network errors,
    # write processing should be written in a callback function,
    # and processing should be done after confirming that
    # communication has ended successfully.
    def empty_callback():
        pass
    DEFAULT_RECV_SIZE = 1024
    def read_line(s: socket.socket, remain_data: bytes, received=False) -> tuple[bytes, bytes, bool]:
        data = remain_data
        while True:
            index_of_crlf = data.find(b"\r\n")
            if index_of_crlf < 0:
                if received:
                    return data, b"", received
                recv = s.recv(DEFAULT_RECV_SIZE)
                data += recv
                if len(recv) < DEFAULT_RECV_SIZE:
                    received = True
            else:
                return data[:index_of_crlf], data[index_of_crlf + 2:], received
    try:
        first_line, remain_data, received = read_line(cl, b"")
        first_line_splitted = first_line.split(b" ")
        method = first_line_splitted[0].decode()
        path_and_query = first_line_splitted[1].decode()
        path = path_and_query.split("?")[0]
        line = b""
        while True:
            line, remain_data, received = read_line(cl, remain_data, received)
            if len(line) == 0 or received and len(remain_data) == 0:
                break

        if method == "PUT":
            def move_callback(before_path: str, after_path: str):
                def rename():
                    mkdir_filename(after_path)
                    os.rename(before_path, after_path)
                    rm_recursive("/tmp")
                return rename
            tmp_path = "/tmp" + path

            mkdir_filename(tmp_path)
            with open(tmp_path, "wb") as f:
                if 0 < len(line):
                    f.write(line)
                f.write(remain_data)
                while True:
                    if received:
                        break
                    new_data = cl.recv(DEFAULT_RECV_SIZE)
                    if new_data:
                        f.write(new_data)
                    else:
                        break
                    if len(new_data) < DEFAULT_RECV_SIZE:
                        break
            return b"HTTP/1.1 201 Created", b"Created", move_callback(tmp_path, path)
        elif method == "DELETE":
            try:
                def rm_callback(path):
                    def rm():
                        rm_recursive(path)
                    return rm
                return b"HTTP/1.1 200 OK", b"OK", rm_callback(path)
            except:
                return b"HTTP/1.1 404 Not Found", b"Not Found", empty_callback
        elif method == "POST":
            if path == "/reset":
                def reset_callback():
                    time.sleep(1)
                    machine.reset()
                return b"HTTP/1.1 200 OK", b"OK", reset_callback
            elif path == "/tar":
                def untar_callback(data):
                    def ut():
                        untar("", data)
                    return ut
                return b"HTTP/1.1 201 Created", b"Created", untar_callback(cl.recv(DEFAULT_RECV_SIZE))
            elif path == "/cleanup":
                def cleanup_callback():
                    cleanup()
                return b"HTTP/1.1 200 OK", b"OK", cleanup_callback
            else:
                return b"HTTP/1.1 404 Not Found", b"Not Found", empty_callback
        else:
            return b"HTTP/1.1 400 Bad Request", b"Bad Request", empty_callback
    except Exception as e:
        sys.print_exception(e)
        return b"HTTP/1.1 500 Internal Server Error", b"Internal Server Error", empty_callback


def start_server():
    """Start TCP server"""
    s = socket.socket()
    s.bind(("0.0.0.0", 9000))
    s.listen()

    while True:
        cl, claddr = s.accept()
        print("Connect:", claddr)

        response, body, callback = http_handler(cl)
        cl.send(response)
        cl.send(b"\r\n\r\n")
        cl.send(body)
        cl.close()
        print("Closed:", claddr)
        callback()

def server_loop():
    while True:
        try:
            start_server()
        except Exception as e:
            sys.print_exception(e)
        time.sleep(1)


# main
wifi_connect()
_thread.start_new_thread(server_loop, ())
start_deployed()
