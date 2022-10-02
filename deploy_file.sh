#!/bin/bash -e

USAGE="Usage: deploy_file.sh [-u user] [-p password] remote_address file_path [destination_path]"

while [[ -n ${1} && ${1} =~ ^- ]]
do
  case ${1} in
    "-u" ) USERNAME=${2}; shift ;;
    "-p" ) PASSWORD=${2}; shift ;;
  esac
  shift
done

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

if [ -n $USERNAME ] && [ -n $PASSWORD ]; then
  curl -X PUT -H "Content-Type: application/octet-stream" --data-binary @${2} "http://${USERNAME}:${PASSWORD}@${1}:9000/${DEST_PATH}"
else
  curl -X PUT -H "Content-Type: application/octet-stream" --data-binary @${2} "http://${1}:9000/${DEST_PATH}"
fi
echo ""
