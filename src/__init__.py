import _thread

import wifi
import deployed
import server

wifi.wifi_connect()

def server_loop():
    while True:
        try:
            server.start_server()
        except Exception as e:
            print(e)

_thread.start_new_thread(server_loop, ())

deployed.start_deployed()
