# MicroPython Script Load Server

## What's this?
Deploying MicroPython code on the board requires connecting it to a PC, which is tedious and time consuming.

This project aim to deploy MicroPython code faster via network.

## How to use this?
### Setup the board
#### With microSD card
##### Copy src contents to the microSD card
Copy all files under the src directory to your microSD card.

##### Connect microSD card to board
First, you have to connect a microSD card to your board.

You can use this script without a microSD card.
But I recommend to use a microSD card.

To connect microSD card to your board, [check this document](https://docs.micropython.org/en/latest/library/machine.SDCard.html).
[日本語版ドキュメント](https://micropython-docs-ja.readthedocs.io/ja/latest/library/machine.SDCard.html)

##### Put main.py to your board
Run `./put_main.sh [serial_port]`.

If you use macOS, `serial_port` will look like `/dev/tty.usbserial-0001`.

Then, Power on your board!

#### Without microSD card
Without microSD card is quite a simple.
But when you update this server code, you have to connect your board to PC.

##### Put all scripts to your board
Run `./put_all.sh [serial_port]`.

Then, Power on your board!

### Deploy your code
You can deploy MicroPython codes in `deploy` directory.

When your board is started, `__init__.py` is loaded first.
So you have to create `deploy/__init__.py` first.

When you are ready to deploy, Run `./deploy.py [serial_port]`.

Your board is automatically reset.
