import os
import socket
from functools import partial

import lirc
import serial

class LircCodeReaderMixin(object):

    def __init__(self, name='PyLirc', config='~/.lircrc', **kwargs):
        self.name = name
        self.config = config
        lirc.init(self.name, self.config)
        super(LircCodeReaderMixin, self).__init__(**kwargs)

    def lirc_commands(self):
        while True:
            for each in lirc.nextcode():
                yield each


class TcpControlMixin(object):

    def __init__(self, ip_address=None, port=8102, **kwargs):
        if not ip_address:
            raise TypeError
        self.tcp_state = {}
        self.connected = False
        self.ip_address = ip_address
        self.port = port
        self.connect_tcp()
        self.update_command_map(self.execute_tcp_command, self.tcp_command_map)
        super(TcpControlMixin, self).__init__(**kwargs)

    tcp_command_map = {
        'KEY_VOLUMEUP': 'VU',
        'KEY_VOLUMEDOWN': 'VD',
        'KEY_MUTE': 'MUTE',
    }

    tcp_toggle_commands = {
        'MUTE': {
            False: 'MO',
            True: 'MF',
        }
    }

    def get_tcp_toggle_state(self, command):
        state = self.tcp_state.get(command, False)
        self.tcp_state[command] = not state
        return self.tcp_toggle_commands[command][state]

    def connect_tcp(self):
        self._tcpsock = socket.socket()
        self._tcpsock.connect((self.ip_address, self.port))
        self.connected = True

    def send_tcp_command(self, command):
        if not self.connected:
            self.connect_tcp()
        try:
            self._tcpsock.send(command)
        except BrokenPipeError:
            self.connected = False
            self.send_tcp_command(command)

    def execute_tcp_command(self, command):
        if command in self.tcp_toggle_commands:
            command = self.get_tcp_toggle_state(command)
        command = command + '\r\n'
        encoded = command.encode('ascii')
        self.send_tcp_command(encoded)


class SerialControlMixin(object):

    def __init__(self, serial_port=None, **kwargs):
        if not serial_port:
            raise TypeError
        self.ser = serial.Serial(serial_port, baudrate=9600, bytesize=8, timeout=3)
        self.update_command_map(self.send_serial_command, self.serial_command_map)
        super(SerialControlMixin, self).__init__(**kwargs)

    serial_command_map = {
        'KEY_HOME': [0x08, 0x22, 0x00, 0x00, 0x00, 0x00, 0xd6]
    }

    def send_serial_command(self, command):
        self.ser.write(command)


class RemoteCommand(LircCodeReaderMixin, TcpControlMixin, SerialControlMixin, object):

    def __init__(self, **kwargs):
        self.command_map = {}
        self.state = {}
        super(RemoteCommand, self).__init__(**kwargs)

    def update_command_map(self, command_method, mapping):
        for key, arg in mapping.items():
            self.command_map[key] = partial(command_method, arg)

    def run(self):
        for code in self.lirc_commands():
            self.command_map[code]()

if __name__ == '__main__':
    tcp_receiver = os.environ['RIKER_TCP_RECEIVER_ADDRESS']
    lirc_name = os.environ['RIKER_LIRC_NAME']
    serial_port = os.environ['RIKER_SERIAL_PORT']
    commander = RemoteCommand(name=lirc_name, ip_address=tcp_receiver, serial_port=serial_port)
    commander.run()
