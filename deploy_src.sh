#!/bin/bash -e

USAGE="Usage: deploy_src.sh remote_address"

if [ -z ${1} ]; then
  echo $USAGE
  exit 1
fi

echo -n "Cleanup..."
curl -X POST "http://${1}:9000/cleanup"
echo ""

BASE_DIR_ABSOLUTE_PATH=$(pwd)/src/
FILE_LIST=$(find $BASE_DIR_ABSOLUTE_PATH -type f | sed -E "s/^.{${#BASE_DIR_ABSOLUTE_PATH}}(.*)/\1/")
for v in $FILE_LIST
do
  echo -n "Send ${v}..."
  ./deploy_file.sh ${1} src/${v} ${v}
done

./reset.sh ${1}
