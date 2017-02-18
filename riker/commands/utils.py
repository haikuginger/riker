import binascii
import socket
from subprocess import Popen, PIPE, STDOUT

import serial
from py_irsend import irsend

SERIAL_CONNECTIONS = {}

TCP_CONNECTIONS = {}

CEC_CLIENT = None


def send_infrared_command(device, command):
    irsend.send_once(device, [command])


def send_serial_command(port, baud, bytesize, timeout, command):
    try:
        ser = SERIAL_CONNECTIONS.pop((port, baud, bytesize, timeout,))
    except KeyError:
        ser = serial.Serial(port, baudrate=baud, bytesize=bytesize, timeout=timeout)
    bytecommand = binascii.unhexlify(command)
    ser.write(bytecommand)
    SERIAL_CONNECTIONS[(port, baud, bytesize, timeout,)] = ser


def send_cec_command(source, sink, command):
    global CEC_CLIENT
    if CEC_CLIENT is None:
        CEC_CLIENT = Popen(
            ['cec-client'],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            bufsize=1,
            universal_newlines=True,
        )
    full_command = 'tx {source}{sink}:44:{command} \n tx {source}{sink}:45 \n'.format(
        source=source,
        sink=sink,
        command=command
    )
    CEC_CLIENT.stdin.write(full_command)


def send_tcp_command(host, port, command, retries=5):
    encoded_command = (command + '\r\n').encode('ascii')
    try:
        conn = TCP_CONNECTIONS.pop((host, port,))
    except KeyError:
        conn = socket.socket()
        conn.connect((host, port))
    try:
        conn.send(encoded_command)
    except BrokenPipeError:
        if retries:
            return send_tcp_command(host, port, command, retries=retries-1)
        else:
            raise
    TCP_CONNECTIONS[(host, port)] = conn