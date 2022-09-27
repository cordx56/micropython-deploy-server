#!/bin/bash -e

USAGE="Usage: reset.sh remote_address"

if [ -z ${1} ]; then
  echo $USAGE
  exit 1
fi

echo -n "Reset..."
curl -X POST "http://${1}:9000/reset"
echo ""
