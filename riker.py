import os
import socket
from functools import partial
from subprocess import Popen, PIPE, STDOUT
from uuid import uuid4

import lirc
import serial

LIRCRC_TEMPLATE = """
begin
        prog   = {lirc_name}
        button = {key_name}
        config = {key_name}
end

"""

class LircCodeReaderMixin(object):

    def __init__(self, name='PyLirc', **kwargs):
        self.name = name
        config = uuid4().hex
        self.config = config
        with open(self.config, 'w') as configfile:
            configfile.write(
                '\n'.join(
                    LIRCRC_TEMPLATE.format(
                        lirc_name=self.name,
                        key_name=key_name
                    ) for key_name in self.command_map
                )
            )
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


class CecControlMixin(object):

    cec_command_map = {
        'KEY_UP': '01',
        'KEY_DOWN': '02',
        'KEY_RIGHT': '04',
        'KEY_LEFT': '03',
        'KEY_SELECT': '00',
        'KEY_BACK': '0D',
        'KEY_MENU': '71',
        'KEY_SUBTITLE': '72',
        'KEY_PVR': '73',
        'KEY_HOME': '09',
        'KEY_CHANNELUP': '37',
        'KEY_CHANNELDOWN': '38',
        'KEY_PLAYPAUSE': '44',
        'KEY_FASTFORWARD': '49',
        'KEY_REWIND': '48',
        'KEY_STOP': '45',
        'KEY_NEXTSONG': '4B',
        'KEY_PREVIOUSSONG': '4C',
    }

    def __init__(self, source_id=1, sink_id=None, **kwargs):
        if not sink_id:
            raise TypeError
        self.cec_source_id = source_id
        self.cec_sink_id = sink_id
        self.cec_client = Popen(
            ['cec-client'],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            bufsize=1,
            universal_newlines=True,
        )
        self.update_command_map(self.send_cec_command, self.cec_command_map)
        super(CecControlMixin, self).__init__(**kwargs)

    def send_cec_command(self, command):
        full_command = 'tx {source}{sink}:44:{command} \n tx {source}{sink}:45 \n'.format(
            source=self.cec_source_id,
            sink=self.cec_sink_id,
            command=command
        )
        self.cec_client.stdin.write(full_command)


class RemoteCommand(TcpControlMixin, SerialControlMixin, CecControlMixin, LircCodeReaderMixin, object):

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
    cec_target = os.environ['RIKER_CEC_TARGET_ID']
    commander = RemoteCommand(
        name=lirc_name,
        ip_address=tcp_receiver,
        serial_port=serial_port,
        sink_id=cec_target,
    )
    commander.run()
