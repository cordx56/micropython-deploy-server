#!/bin/bash -ex

echo "Transferring main.py"
ampy -p ${1} put main.py
