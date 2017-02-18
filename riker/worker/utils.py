from logging import getLogger
import tempfile
from threading import Thread

import lirc
from django.conf import settings

from systemstate.models import RemoteButton
from systemstate.utils import push_button


LOGGER = getLogger(__name__)


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
        self.lircrc_filename = create_lircrc_tempfile()
        super(LircListener, self).__init__()

    def run(self):
        lirc.init(self.lirc_name, self.lircrc_filename)
        listen(self.lirc_name, self.lircrc_filename)


def listen(lirc_name, lircrc_filename, callback=None):
    lirc.init(lirc_name, lircrc_filename)
    callback = callback or push_button
    while True:
        for key_code in lirc.nextcode():
            LOGGER.warning(key_code)
            callback(key_code)


def create_lircrc_tempfile(lirc_name):
    buttons = RemoteButton.objects.all().values_list('lirc_code', flat=True)
    with tempfile.NamedTemporaryFile(delete=False) as lircrc_file:
        lircrc_file.write(generate_lircrc(lirc_name, buttons).encode('ascii'))
        return lircrc_file.name


def generate_lircrc(name, buttons):
    return '\n'.join(
        LIRCRC_TEMPLATE.format(
            lirc_name=name,
            key_name=button,
        ) for button in buttons
    )