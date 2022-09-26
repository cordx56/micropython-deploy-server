# MicroPython Script Server

## What's this?
Deploying MicroPython code on the board requires connecting it to a PC, which is tedious and time consuming.

This project aim to deploy MicroPython code faster via network.

## Requirements
These need to be installed on your PC:
- curl
- ampy
  - `pip install adafruit-ampy`

## How to use this?
### Setup the board
#### Install MicroPython
Install MicroPython to your board.

The guide can be found [here](https://docs.micropython.org/en/latest/index.html).
日本語版ガイドは[こちら](https://micropython-docs-ja.readthedocs.io/ja/latest/index.html)。
#### Edit secrets.py
Edit `src/secrets.py` to enable WiFi connection.

Example:
```python
WIFI_SSID = "your WiFi SSID"
WIFI_PASSWORD = "your WiFi password"

WIFI_IFCONFIG = None
# You can specify static IPv4 address
# (If you not specify static IPv4 address, IPv4 address is determined using DHCP)
# WIFI_IFCONFIG = ("192.168.1.1", "255.255.255.0", "192.168.1.1", "8.8.8.8")
```
#### Put main.py and secrets.py to your board
Run `./put.sh [serial]`.

If you use macOS, `serial` will look like `/dev/tty.usbserial-0001`.

Then, Power on your board!

### How to deploy the program?
Use `deploy_src.sh`.
This script will automatically transfer files under src directory via network and reset your board.

When your board is reset, `main.py` opens `init.py` and run the contents.
This means that the entry point for your program must be written in `src/init.py`.

## How to use API?
The API is simple.
Server listing TCP port 9000.
You can send HTTP request to the server.

### POST [path]
You can deploy your script to specified path.

Example:
```bash
$ curl -X POST -H "Content-Type: application/octet-stream" --data-binary @src/init.py "http://192.168.1.102:9000/init.py"
```

### DELETE [path]
Delete specified file.

Example:
```bash
$ curl -X DELETE http://192.168.1.102:9000/init.py"
```

### POST /reset
Reset your board.

Example:
```bash
$ curl -X POST http://192.168.1.102:9000/reset"
```

### POST /tar
Deploy tar file.

Example:
```bash
$ curl -X POST -H "Content-Type: application/octet-stream" --data-binary @deploy.tar "http://192.168.1.102:9000/tar"
```
