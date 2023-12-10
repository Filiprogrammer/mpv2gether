#!/usr/bin/env python3

import sys
import socket
import time
import subprocess

mpv = subprocess.Popen(
    ["mpv", sys.argv[1], "--input-ipc-server=/tmp/mpvsocket", "--pause"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.STDOUT
)

time.sleep(1)

mpvclient = socket.socket(socket.AF_UNIX)
mpvclient.connect("/tmp/mpvsocket")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (sys.argv[2], int(sys.argv[3]))
print("Connecting to " + str(server_address) + "...")
client.connect(server_address)
print("Connected")

while True:
    data = client.recv(1024)

    if len(data) == 0:
        break

    print("Received from server: " + str(data))

    if data.startswith(b"pause"):
        mpvclient.send(b'{"command":["set_property","pause",true]}\n')
    elif data.startswith(b"play"):
        mpvclient.send(b'{"command":["set_property","pause",false]}\n')
    elif data.startswith(b"seek"):
        mpvclient.send(b'{"command":["set_property","time-pos",' + data.strip().split(b' ')[1] + b']}\n')

client.close()
print("Connection to server closed")
mpv.kill()
