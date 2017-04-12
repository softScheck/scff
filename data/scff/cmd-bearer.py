#!/usr/bin/env python3

import socket
from sys import argv

if len(argv) < 2:
    print(argv[0], "part of scff - send commands to pineapple")
    print("Usage:", argv[0], "PINEAPPLE_CMD [-d|--debug]")
    exit()

DEBUG = "-d" in argv or "--debug" in argv

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_address = ("localhost", 5555)
if DEBUG:
    print("connecting to %s port %s" % server_address)

try:
    sock.connect(server_address)
except:
    print("ERROR: Can not connect to pineapple daemon. Is the daemon running?")
    exit()

try:
    # Send data
    message = argv[1]
    if DEBUG:
        print("sending '%s'" % message)
    sock.sendall(bytes(message.encode("UTF-8")))
    amount_received = 0
    amount_expected = 1024
    data = sock.recv(amount_expected)
    amount_received += len(data)
    print(data.decode("UTF-8"))
finally:
    if DEBUG:
        print("closing socket")
    sock.close()
