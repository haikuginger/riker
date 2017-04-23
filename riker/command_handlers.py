import binascii
import socket
from subprocess import Popen, PIPE, STDOUT
from time import sleep

import serial
from py_irsend import irsend

SERIAL_CONNECTIONS = {}

TCP_CONNECTIONS = {}

CEC_CLIENT = Popen(
    ['cec-client'],
    stdin=PIPE,
    bufsize=1,
    universal_newlines=True,
)


class BaseCommandHandler(object):

    def set_default_handlers(self):
        if not hasattr(self, 'command_handlers'):
            self.command_handlers = {}


class InfraredMixin(BaseCommandHandler):
    
    def __init__(self, *args, **kwargs):
        self.set_default_handlers()
        self.command_handlers['infrared'] = self.send_infrared_command
        super(InfraredMixin, self).__init__(*args, **kwargs)

    def send_infrared_command(self, device, command):
        irsend.send_once(device, [command])


class SerialMixin(BaseCommandHandler):

    def __init__(self, *args, **kwargs):
        self.set_default_handlers()
        self.command_handlers['serial'] = self.send_serial_command
        super(SerialMixin, self).__init__(*args, **kwargs)

    def send_serial_command(self, port, baud, bytesize, timeout, command):
        try:
            ser = SERIAL_CONNECTIONS.pop((port, baud, bytesize, timeout,))
        except KeyError:
            ser = serial.Serial(port, baudrate=baud, bytesize=bytesize, timeout=timeout)
        bytecommand = binascii.unhexlify(command)
        ser.write(bytecommand)
        SERIAL_CONNECTIONS[(port, baud, bytesize, timeout,)] = ser


class CecMixin(BaseCommandHandler):

    def __init__(self, *args, **kwargs):
        self.set_default_handlers()
        self.command_handlers['cec'] = self.send_cec_command
        super(CecMixin, self).__init__(*args, **kwargs)

    def send_cec_command(self, source, sink, command):
        full_command = 'tx {source}{sink}:44:{command} \n tx {source}{sink}:45 \n'.format(
            source=source,
            sink=sink,
            command=command
        )
        CEC_CLIENT.stdin.write(full_command)


class TcpMixin(BaseCommandHandler):

    def __init__(self, *args, **kwargs):
        self.set_default_handlers()
        self.command_handlers['tcp'] = self.send_tcp_command
        super(TcpMixin, self).__init__(*args, **kwargs)

    def send_tcp_command(self, host, port, command, retries=5):
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
