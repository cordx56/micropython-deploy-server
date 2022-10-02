#!/bin/bash -e

USAGE="Usage: deploy.sh [--dry-run] [-u user] [-p password] remote_address [base_dir]"

while [[ -n ${1} && ${1} =~ ^- ]]
do
  case ${1} in
    "--dry-run" ) DRY_RUN=1 ;;
    "-u" ) USERNAME=${2}; shift ;;
    "-p" ) PASSWORD=${2}; shift ;;
  esac
  shift
done

if [ -z ${1} ]; then
  echo $USAGE
  exit 1
fi

SCRIPT_DIR=$(cd $(dirname $0); pwd)
if [ -z ${2} ]; then
  BASE_DIR_ABS_PATH=$SCRIPT_DIR/src
else
  BASE_DIR_ABS_PATH=$(cd ${2}; pwd)
fi

echo -n "Cleanup..."
if [ -z $DRY_RUN ]; then
    if [ -n $USERNAME ] && [ -n $PASSWORD ]; then
      curl -X POST "http://${USERNAME}:${PASSWORD}@${1}:9000/cleanup"
    else
      curl -X POST "http://${1}:9000/cleanup"
    fi
fi
echo ""

FILE_LIST=$(find $BASE_DIR_ABS_PATH -type f | sed -E "s/^.{$((${#BASE_DIR_ABS_PATH} + 1))}(.*)/\1/")
for v in $FILE_LIST
do
  echo -n "Send ${v}..."
  if [ -z $DRY_RUN ]; then
    if [ -n $USERNAME ] && [ -n $PASSWORD ]; then
      $SCRIPT_DIR/deploy_file.sh -u ${USERNAME} -p $PASSWORD ${1} $BASE_DIR_ABS_PATH/${v} ${v}
    else
      $SCRIPT_DIR/deploy_file.sh ${1} $BASE_DIR_ABS_PATH/${v} ${v}
    fi
  else
    echo ""
  fi
done

echo -n "Reset..."
if [ -z $DRY_RUN ]; then
    if [ -n $USERNAME ] && [ -n $PASSWORD ]; then
      curl -X POST "http://${USERNAME}:${PASSWORD}@${1}:9000/reset"
    else
      curl -X POST "http://${1}:9000/reset"
    fi
fi
echo ""
