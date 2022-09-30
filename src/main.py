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



# myhttp
class SendHeaderAfterBodyError(Exception):
    pass
class HeaderFormatError(Exception):
    pass
class HeaderFinishedError(Exception):
    pass
class HTTPFormatError(Exception):
    pass

class SocketReader:
    client: socket.socket
    buffer: bytes = b""
    received: bool = False
    DEFAULT_RECV_SIZE = 1024
    def __init__(self, client: socket.socket):
        self.client = client
    def recv(self, size=DEFAULT_RECV_SIZE):
        if self.received:
            return b""
        recv = self.client.recv(size)
        self.buffer += recv
        if len(recv) < size:
            self.received = True
        return recv
    def read_line(self, line_end=b"\n") -> bytes:
        while True:
            index_of_crlf = self.buffer.find(line_end)
            if index_of_crlf < 0:
                if self.received:
                    ret = self.buffer
                    self.buffer = b""
                    return ret
                self.recv()
            else:
                line = self.buffer[:index_of_crlf + len(line_end)]
                self.buffer = self.buffer[index_of_crlf + len(line_end):]
                return line
    def read_line_without_line_end(self, line_end=b"\n") -> bytes:
        line = self.read_line(line_end)
        if len(line_end) <= len(line) and line[-len(line_end):] == line_end:
            return line[:-(len(line_end))]
        return line
    def read(self, size=-1):
        if size < 0:
            while not self.received:
                self.recv()
            ret = self.buffer
            self.buffer = b""
            return ret
        else:
            while len(self.buffer) < size:
                if not self.recv():
                    break
            ret = self.buffer[:size]
            if len(ret) < size:
                self.buffer = b""
            else:
                self.buffer = self.buffer[size:]
            return ret

class HTTPRequest:
    method: str
    path: str
    query: str
    proto: str
    reader: SocketReader
    header_finished: bool = False
    def __init__(self, method: str, path: str, query: str, proto: str, reader: SocketReader):
        self.method = method
        self.path = path
        self.query = query
        self.proto = proto
        self.reader = reader
    def read_header(self) -> tuple[str, str] | None:
        if self.header_finished:
            raise HeaderFinishedError
        header_line = self.reader.read_line_without_line_end(b"\r\n")
        if len(header_line) == 0:
            self.header_finished = True
            return None
        index_of_colon = header_line.find(b":")
        if index_of_colon < 0:
            raise HeaderFormatError
        header_name = header_line[:index_of_colon]
        value = header_line[:index_of_colon].strip()
        return header_name.decode(), value.decode()
    def read_body(self, size=-1) -> bytes:
        return self.reader.read(size)

HTTP_STATUS = {
    200: "OK",
    201: "Created",
    301: "Moved Permanently",
    302: "Found",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    500: "Internal Server Error",
}
class HTTPResponse:
    header_finish = False
    client: socket.socket
    def __init__(self, client: socket.socket):
        self.client = client

    def send_status(self, status: int):
        self.client.send(f"HTTP/1.1 {status} {HTTP_STATUS[status]}\r\n".encode())
    def send_header(self, name: str, value: str):
        if self.header_finish:
            raise SendHeaderAfterBodyError
        self.client.send(name.encode() + b": " + value.encode() + b"\r\n")
    def send_body(self, body: bytes):
        if not self.header_finish:
            self.header_finish = True
            self.client.send(b"\r\n")
        self.client.send(body)

class HTTPServer:
    s: socket.socket
    debug: bool
    handlers = {}
    def __init__(self, port: int, debug=False) -> None:
        self.debug = debug
        self.s = socket.socket()
        self.s.bind(("0.0.0.0", port))
    def listen(self):
        self.s.listen()
        while True:
            cl, claddr = self.s.accept()
            callback = None
            try:
                if self.debug:
                    print("Connect from:", claddr)
                http_request = self.get_request(cl)
                http_response = HTTPResponse(cl)

                try:
                    callback = self.handlers[http_request.method][http_request.path](http_request, http_response)
                except KeyError:
                    wildcard_handler = None
                    method_handlers = self.handlers.get(http_request.method)
                    if method_handlers:
                        wildcard_handler = method_handlers.get("")

                    if wildcard_handler:
                        callback = wildcard_handler(http_request, http_response)
                    elif self.not_found_handler:
                        self.not_found_handler(http_request, http_response)
                    else:
                        pass
            finally:
                cl.close()
            if callback:
                callback()


    def on(self, method: str, path: str, handler) -> None:
        self.handlers.setdefault(method, {})
        self.handlers[method][path] = handler
    def on_not_found(self, handler) -> None:
        self.not_found_handler = handler

    def get_request(self, cl: socket.socket) -> HTTPRequest:
        # parse first line
        sr = SocketReader(cl)
        try:
            line = sr.read_line_without_line_end(b"\r\n")
            line = line.decode()
            if self.debug:
                print(line)
            line_splitted = line.split(" ")
            method = line_splitted[0]
            path_query = line_splitted[1]
            proto = line_splitted[2]
            pq_splitted = path_query.split("?")
            path = pq_splitted[0]
            if 1 < len(pq_splitted):
                query = pq_splitted[1]
            else:
                query = ""
        except:
            raise HTTPFormatError
        return HTTPRequest(method, path, query, proto, sr)
# myhttp end

def handle_not_found(req: HTTPRequest, res: HTTPResponse):
    res.send_status(404)
    res.send_header("Content-Type", "text/plain")
    res.send_body(b"Not Found")

def handle_put_file(req: HTTPRequest, res: HTTPResponse):
    def move_callback(before_path: str, after_path: str):
        def rename():
            mkdir_filename(after_path)
            os.rename(before_path, after_path)
            rm_recursive("/tmp")
        return rename
    tmp_path = "/tmp" + req.path
    try:
        while req.read_header():
            pass
        mkdir_filename(tmp_path)
        with open(tmp_path, "wb") as f:
            while True:
                recv = req.read_body(SocketReader.DEFAULT_RECV_SIZE)
                if not recv:
                    break
                f.write(recv)
        res.send_status(201)
        res.send_header("Content-Type", "text/plain")
        res.send_body(b"Created")
        return move_callback(tmp_path, req.path)
    except:
        res.send_status(500)
        res.send_header("Content-Type", "text/plain")
        res.send_body(b"Internal Server Error")
def handle_delete_file(req: HTTPRequest, res: HTTPResponse):
    try:
        rm_recursive(req.path)
        res.send_status(200)
        res.send_header("Content-Type", "text/plain")
        res.send_body(b"OK")
    except:
        res.send_status(500)
        res.send_header("Content-Type", "text/plain")
        res.send_body(b"Internal Server Error")
def handle_reset(req: HTTPRequest, res: HTTPResponse):
    def reset_callback():
        time.sleep(1)
        machine.reset()
    res.send_status(200)
    res.send_header("Content-Type", "text/plain")
    res.send_body(b"OK")
    return reset_callback
def handle_cleanup(req: HTTPRequest, res: HTTPResponse):
    try:
        cleanup()
        res.send_status(200)
        res.send_header("Content-Type", "text/plain")
        res.send_body(b"OK")
    except:
        res.send_status(500)
        res.send_header("Content-Type", "text/plain")
        res.send_body(b"Internal Server Error")

s = HTTPServer(9000)
s.on_not_found(handle_not_found)
s.on("PUT", "", handle_put_file)
s.on("DELETE", "", handle_delete_file)
s.on("POST", "/reset", handle_reset)
s.on("POST", "/cleanup", handle_cleanup)

def start_server():
    s.listen()

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
