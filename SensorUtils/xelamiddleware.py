#!/usr/bin/env python3.8
import websocket
import websockets
import asyncio
import json
import threading
import importlib

#console printing related
import subprocess
subprocess.call('', shell=True)

websocket.setdefaulttimeout(1) #you should avoid increasing it.
#set up argument parser
def threader(target, args=False, **targs):
    if args:
        targs["args"]=(args,)
    thr = threading.Thread(target=target, **targs, daemon=True)
    thr.start()
    return thr

class XELA_Settings(object):
    def __init__(self, client_ip="127.0.0.1", server_ip = "127.0.0.1", client_port= 5000, server_port=5001):
        self.__client_ip = client_ip
        self.__server_ip = server_ip
        self.__client_port = client_port
        self.__server_port = server_port
    def get_client(self):
        return (self.__client_ip,self.__client_port)
    def get_server(self):
        return (self.__server_ip,self.__server_port)
    def __get_ip(self, setIP=None):
        socket = importlib.import_module("socket")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('1.2.3.4', 1))
            IP = s.getsockname()
        except Exception:
            IP = ['127.0.0.1']
        finally:
            s.close()
        return IP[0]
    def iamclient(self):
        self.__client_ip = self.__get_ip()
    def iamserver(self):
        self.__server_ip = self.__get_ip()

class XELA_Server(object):
    def __init__(self, settings=None,datafunction=None):
        self.settings = settings if settings is not None else XELA_Settings()
        self.data = datafunction if datafunction is not None else self.emptyfunc
        self.main()
    def emptyfunc(self):
        return {}
    def close(self):
        try:
            self.loop.stop()
            self.loop.stop()
            self.loop.close()
        except Exception:
            pass
    async def connection(self, websocket, path):
        print("\033[32m{}\033[0m connected".format(websocket))
        try:
            while int(websocket.state) == 1:
                await websocket.send(json.dumps(self.data()))
                await asyncio.sleep(0.000005)
        except Exception as e:
            print("EXP: {}: {}".format(type(e).__name__,e))
        finally:
            print("\033[31m{}\033[0m disconnected".format(websocket))
    def server_loop(self):
        print("Server started")
        self.loop.run_until_complete(self.server)
        print("Server midpoint")
        self.loop.run_forever()

        print("Server ended")
    def main(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.server = websockets.serve(self.connection, *self.settings.get_server())
        threader(self.server_loop,name="Server_Thread")

class XELA_Client(object):
    def __init__(self, settings=None,runfunction=None):
        self.settings = settings if settings is not None else XELA_Settings()
        self.runfunc = runfunction if runfunction is not None else self.emptyfunc
        self.__data = []
        self.main()
    def emptyfunc(self,data):
        _ = data
    def on_message(self,wsapp, message):
        try:
            data = json.loads(message)
        except Exception:
            pass
        else:
            try:
                if data["message"] == "Welcome":
                    print(data)
                else:
                    self.__data = data
                    self.runfunc(data)
            except Exception:
                pass
    def getData(self):
        return self.__data
    def close(self):
        print("Trying to close Client")
        try:
            self.client.close()
        except Exception:
            pass
    def main(self):
        self.client = websocket.WebSocketApp("ws://{}:{}".format(*self.settings.get_client()), on_message=self.on_message)
        self.client_thread = threader(self.client.run_forever,name="Client_Thread")
        print("Client started")
 