#!/bin/bash -e

USAGE="Usage: deploy_file.sh remote_address file_path [destination_path]"

if [ -z ${1} ]; then
  echo $USAGE
  exit 1
fi

if [ -z ${2} ]; then
  echo $USAGE
  exit 1
fi

if [ -z ${3} ]; then
  DEST_PATH=${2}
else
  DEST_PATH=${3}
fi

curl -X PUT -H "Content-Type: application/octet-stream" --data-binary @${2} "http://${1}:9000/${DEST_PATH}"
echo ""
