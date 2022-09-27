#!/bin/bash -e

USAGE="Usage: deploy_src.sh remote_address"

if [ -z ${1} ]; then
  echo $USAGE
  exit 1
fi

echo -n "Cleanup..."
curl -X POST "http://${1}:9000/cleanup"
echo ""

cd src
tar -cvf ../deploy.tar $(ls)

echo -n "Send..."
curl -X POST -H "Content-Type: application/octet-stream" --data-binary @../deploy.tar "http://${1}:9000/tar"
echo ""

cd ..
rm -f deploy.tar
./reset.sh ${1}
