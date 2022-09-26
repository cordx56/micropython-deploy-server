#!/bin/bash -e

USAGE="Usage: reset.sh remote_address"

if [ -z ${1} ]; then
  echo $USAGE
  exit 1
fi

curl "http://${1}:9000/reset"
echo ""
