#!/bin/bash -ex

echo "Transferring main.py"
ampy -p ${1} put main.py
cd src
for file in $(ls *.py); do
  echo "Transferring ${file}"
  ampy -p ${1} put ${file}
done
