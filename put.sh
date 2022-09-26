#!/bin/bash -e

cd src
echo "Transferring main.py"
ampy -p ${1} put main.py
echo "Transferring secrets.py"
ampy -p ${1} put secrets.py
