#!/usr/bin/env python3

import json
import socket
import subprocess
import sys
import time

PORT = 1310

mpv = subprocess.Popen(
    ["mpv", sys.argv[1], "--input-ipc-server=/tmp/mpvsocket", "--pause"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.STDOUT
)

time.sleep(1)

mpvclient = socket.socket(socket.AF_UNIX)
mpvclient.connect("/tmp/mpvsocket")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', PORT))
server.listen(1)
print("Waiting for a connection")
connection, client_address = server.accept()
print(str(client_address) + " connected")

mpvclient.send(b'{"command":["observe_property",1,"pause"]}\n')

while True:
    mpvmsg = b""
    connected = True

    while True:
        c = mpvclient.recv(1)

        if len(c) == 0:
            connected = False
            break

        if c == b'\n':
            break

        mpvmsg += c

    if not connected:
        break

    print("Received from mpv: " + str(mpvmsg))

    try:
        mpvmsgjson = json.loads(mpvmsg)

        if "event" in mpvmsgjson:
            if mpvmsgjson["event"] == "property-change":
                if mpvmsgjson["name"] == "pause":
                    if mpvmsgjson["data"] == True:
                        connection.send(b"pause\n")
                    else:
                        connection.send(b"play\n")
            elif mpvmsgjson["event"] == "seek":
                time.sleep(0.1)
                mpvclient.setblocking(False)
                while True:
                    try:
                        mpvclient.recv(1024)
                    except:
                        break
                mpvclient.setblocking(True)
                mpvclient.send(b'{"command":["get_property","time-pos"]}\n')
                mpvmsg = mpvclient.recv(1024)
                print("Seek: " + str(mpvmsg))
                mpvmsgjson = json.loads(mpvmsg)
                print("mpvmsgjson: " + str(mpvmsgjson))
                connection.send(bytes("seek " + str(mpvmsgjson["data"]) + "\n", "utf-8"))

    except Exception as error:
        print("An error occured: ", error)

connection.close()
server.shutdown(socket.SHUT_RDWR)
server.close()
