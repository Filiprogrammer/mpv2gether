# mpv2gether

Very simple Python script to play a local video synchronously with someone else over the network. There is a server and a client. Both parties need to have the video file they want to watch stored locally. Once the client is connected to the server, the server can play and pause the video, as well as seek to any position in the video. These actions are mirrored back to the client. Note that only the server can control the client and not vice versa.

## Dependencies

- python3
- mpv

## Usage

Start the server on port 1310 by default

```console
./server.py /path/to/video.mkv
```

Connect the client to the server

```console
./client.py /path/to/video.mkv <ip address of the server> <port of the server>
```

Both the client and server will now have mpv with the video open and paused at the beginning. Now the server can start playing, pausing and seeking to their heart's content, all synchronised with the client.
