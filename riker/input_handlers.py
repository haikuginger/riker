import lirc

LIRCRC_TEMPLATE = '''
begin
        prog   = {lirc_name}
        button = {key_name}
        config = {key_name}
        repeat = 2
        delay = 3
end

'''

def generate_lircrc(name, buttons):
    return '\n'.join(
        LIRCRC_TEMPLATE.format(
            lirc_name=name,
            key_name=button,
        ) for button in buttons
    )

class LircInputHandlerMixin(object):

    def __init__(self, lirc_name=None, **kwargs):
        super(LircInputHandlerMixin, self).__init__(**kwargs)
        self.lirc_name = lirc_name or 'riker'
        self.lircrc_filename = self.generate_lircrc_tempfile()

    def get_button_presses(self):
        lirc.init(self.lirc_name, self.lircrc_filename)
        while True:
            for key_code in lirc.nextcode():
                LOGGER.warning(key_code)
                yield 'lirc', key_code

    def generate_lircrc_tempfile(self):
        lirc_buttons = []
        for btn_type, btn_name in self.buttons:
            if btn_type == 'lirc':
                lirc_buttons.append(btn_name)
        with tempfile.NamedTemporaryFile(delete=False) as lircrc_file:
            lircrc_file.write(generate_lircrc(self.lirc_name, lirc_buttons).encode('ascii'))
            return lircrc_file.name
