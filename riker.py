import os
import socket
from functools import partial

import lirc

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
        self.connected = False
        self.ip_address = ip_address
        self.port = port
        self.connect_tcp()
        self.update_command_map(self.execute_tcp_command, self.tcp_command_map)
        super(TcpControlMixin, self).__init__(**kwargs)

    tcp_command_map = {
        'KEY_VOLUMEUP': 'VU',
        'KEY_VOLUMEDOWN': 'VD',
    }

    def connect_tcp(self):
        self._tcpsock = socket.socket()
        self._tcpsock.connect((self.ip_address, self.port))
        self.connected = True

    def send_tcp_command(self, command):
        if not self.connected:
            self.connect_tcp()
        self._tcpsock.send(command)

    def execute_tcp_command(self, command):
        command = command + '\r\n'
        encoded = command.encode('ascii')
        self.send_tcp_command(encoded)


class RemoteCommand(LircCodeReaderMixin, TcpControlMixin, object):

    def __init__(self, **kwargs):
        self.command_map = {}
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
    commander = RemoteCommand(name=lirc_name, ip_address=tcp_receiver)
    commander.run()