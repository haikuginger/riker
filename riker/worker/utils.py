import tempfile
from threading import Thread

import lirc
from django.conf import settings

from systemstate.models import RemoteButton
from systemstate.utils import push_button


LIRCRC_TEMPLATE = '''
begin
        prog   = {lirc_name}
        button = {key_name}
        config = {key_name}
end

'''


class LircListener(Thread):

    def __init__(self, lirc_name):
        self.lirc_name = lirc_name
        buttons = RemoteButton.objects.all().values_list('lirc_code', flat=True)
        with tempfile.NamedTemporaryFile(delete=False) as lircrc_file:
            lircrc_file.write(generate_lircrc(self.lirc_name, buttons).encode('ascii'))
            self.lircrc_filename = lircrc_file.name
        super(LircListener, self).__init__()

    def run(self):
        lirc.init(self.lirc_name, self.lircrc_filename)
        while True:
            for key_code in lirc.nextcode():
                push_button(key_code)


def generate_lircrc(name, buttons):
    return '\n'.join(
        LIRCRC_TEMPLATE.format(
            lirc_name=name,
            key_name=button,
        ) for button in buttons
    )