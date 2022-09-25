import os
import json
import binascii

from untar import untar

# GET /
def get_root(headers, body):
    return "200 OK", '{"status":true}'

# POST /api/v1/deploy
def post_deploy(headers, body):
    print(body)
    payload = json.loads(body)
    data = payload["file"]
    try:
        os.mkdir("deploy")
    except:
        pass
    tar = binascii.a2b_base64(data)
    untar("deploy/", tar)
    return "201 Created", '{"status":true}'


endpoints = {
    "GET": {
        "/": get_root,
    },
    "POST": {
        "/api/v1/deploy": post_deploy,
    },
}
