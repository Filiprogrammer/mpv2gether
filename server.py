#!/usr/bin/env python3

import json
import os
import socket
import subprocess
import sys
import threading
import time

PORT = 1310

class MPV:
    def __init__(self, video_file_path, on_play, on_pause, on_seek, on_exit):
        self.process = subprocess.Popen(
            ["mpv", video_file_path, "--input-ipc-server=/tmp/mpv2gether_server_socket", "--pause"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT
        )

        time.sleep(1)
        self.mpvclient = socket.socket(socket.AF_UNIX)
        self.mpvclient.connect("/tmp/mpv2gether_server_socket")
        self.on_play = on_play
        self.on_pause = on_pause
        self.on_seek = on_seek
        self.on_exit = on_exit
        self.paused = True
        self.time = 0.0
        event_listener_thread = threading.Thread(target=self.__listen_for_events)
        event_listener_thread.start()

    def __listen_for_events(self):
        self.mpvclient.sendall(b'{"command":["observe_property",1,"pause"]}\n')

        while True:
            mpvmsg = b""
            connected = True

            while True:
                c = self.mpvclient.recv(1)

                if len(c) == 0:
                    connected = False
                    break

                if c == b'\n':
                    break

                mpvmsg += c

            if not connected:
                print("[MPV] mpv has exited")
                self.on_exit()
                break

            print("[MPV] Received from mpv: " + str(mpvmsg))

            try:
                mpvmsgjson = json.loads(mpvmsg)

                if "event" in mpvmsgjson:
                    if mpvmsgjson["event"] == "property-change":
                        if mpvmsgjson["name"] == "pause":
                            if mpvmsgjson["data"] == True:
                                self.paused = True
                                print("[MPV] Received pause event")
                                self.on_pause()
                            else:
                                self.paused = False
                                print("[MPV] Received play event")
                                self.on_play()
                    elif mpvmsgjson["event"] == "seek":
                        time.sleep(0.1)
                        self.mpvclient.setblocking(False)
                        while True:
                            try:
                                self.mpvclient.recv(1024)
                            except:
                                break
                        self.mpvclient.setblocking(True)
                        self.mpvclient.sendall(b'{"command":["get_property","time-pos"]}\n')
                        mpvmsg = self.mpvclient.recv(1024)
                        print("[MPV] Received seek to " + str(mpvmsg) + " event")
                        mpvmsgjson = json.loads(mpvmsg)
                        self.time = mpvmsgjson["data"]
                        self.on_seek(self.time)

            except Exception as error:
                print("[MPV] An error occured: ", error)

    def play(self):
        if self.paused:
            self.mpvclient.sendall(b'{"command":["set_property","pause",false]}\n')
            self.paused = False

    def pause(self):
        if not self.paused:
            self.mpvclient.sendall(b'{"command":["set_property","pause",true]}\n')
            self.paused = True

    def seek(self, time):
        if self.time != time:
            self.mpvclient.sendall(b'{"command":["set_property","time-pos",' + bytes(str(time), "utf-8") + b']}\n')
            self.time = time


server = None
connection = None
connection_lock = threading.Lock()

def on_play():
    if connection != None:
        with connection_lock:
            connection.sendall(b"play\n")

def on_pause():
    if connection != None:
        with connection_lock:
            connection.sendall(b"pause\n")

def on_seek(time):
    if connection != None:
        with connection_lock:
            connection.sendall(bytes("seek " + str(time) + "\n", "utf-8"))

def on_exit():
    if connection != None:
        connection.close()

    if server != None:
        server.shutdown(socket.SHUT_RDWR)
        server.close()

    os._exit(0)

def ping_task():
    while True:
        with connection_lock:
            connection.sendall(b"ping\n")

        time.sleep(5)

mpv = MPV(sys.argv[1], on_play, on_pause, on_seek, on_exit)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('0.0.0.0', PORT))
server.listen(1)

while True:
    print("Waiting for a connection")
    connection, client_address = server.accept()
    print(str(client_address) + " connected")

    ping_task_thread = threading.Thread(target=ping_task)
    ping_task_thread.start()

    try:
        while True:
            msg = b""
            connected = True

            while True:
                c = connection.recv(1)

                if len(c) == 0:
                    connected = False
                    break

                if c == b'\n':
                    break

                msg += c

            if not connected:
                print(str(client_address) + " disconnected")
                connection.close()
                break

            print("Received from server: " + str(msg))

            if msg.startswith(b"pause"):
                mpv.pause()
            elif msg.startswith(b"play"):
                mpv.play()
            elif msg.startswith(b"seek"):
                seek_time = msg.strip().split(b' ')[1]
                mpv.seek(float(seek_time))
    except:
        pass

    print("Waiting for ping to fail...")
    ping_task_thread.join()
    print("Ping task exited")
