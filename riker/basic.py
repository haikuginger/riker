import json
import logging
import tempfile


LOGGER = logging.getLogger(__name__)

LIRCRC_TEMPLATE = '''
begin
        prog   = {lirc_name}
        button = {key_name}
        config = {key_name}
        repeat = 2
        delay = 3
end

'''


def load_all(config_name, state_name):
    with open(config_name, 'r') as config:
        config = json.load(config)
    config = load_config(config)
    with open(state_name, 'r') as state:
        state = json.load(state)
    state = state['active_states']
    config.update(active_states=state)
    return Riker(**config)

def all_return_true(functions):
    return all (x() for x in functions) if functions else True

def run_all(functions):
    cleanup = []
    for each in functions:
        if each is not None:
            cleanup.append(each())
    return cleanup

def generate_lircrc(name, buttons):
    return '\n'.join(
        LIRCRC_TEMPLATE.format(
            lirc_name=name,
            key_name=button,
        ) for button in buttons
    )

class Riker(object):

    def __init__(self, **config):
        self.config = config
        self.active_states = set(self.config.get('active_states', []))
        self.buttons = {
            ('lirc', button['lirc_code']): self.process_button(button) for button in config.get('buttons', [])
        }

    def get_by_id(self, config_key, item_id):
        items = self.config.get(config_key)
        for item in items:
            if item['id'] == item_id:
                return item
        else:
            return None

    def process_button(self, button):
        command_runner = self.get_command_runner(button.get('commands', []))
        return lambda: command_runner()

    def get_condition_checker(self, condition_id):
        condition = self.get_by_id('conditions', condition_id) or {}
        required_states = set(condition.get('required_states', []))
        required_conditions = condition.get('required_conditions', [])
        required_condition_checkers = [self.get_condition_checker(cond_id) for cond_id in required_conditions]
        
        def state_checker():
            return required_states <= self.active_states
        
        def condition_checker():
            return all_return_true(required_condition_checkers)

        return lambda: bool(state_checker() and condition_checker())

    def get_command_runner(self, commands):
        def run_all_commands():
            cleanup = run_all(runners)
            run_all(cleanup)
        runners = []
        for command in commands:
            runners.append(self.get_single_command_runner(command))
        return run_all_commands

    def get_single_command_runner(self, command_id):
        def run_command():
            if condition_check():
                print('Command of type {} executing: {}'.format(command['type'], command['kwargs']))
                return lambda: run_all(side_effects)
        command = self.get_by_id('commands', command_id)
        if command is None:
            return lambda: None
        else:
            condition_check = self.get_condition_checker(command.get('condition'))
            side_effects = [self.get_state_setter(state) for state in command.get('side_effects', [])]
            return run_command

    def press_button(self, button_id, button_type='lirc'):
        self.buttons.get((button_type, button_id), lambda: None)()

    def get_state_setter(self, state_id):
        def state_setter():
            state_clearer()
            self.active_states.add(state_id)
        state = self.get_by_id('states', state_id)
        if not state:
            return lambda: None
        state_set = state.get('set')
        state_clearer = self.get_state_set_clearer(state_set)
        return state_setter

    def get_state_set_clearer(self, state_set_id):
        def clear_states():
            self.active_states -= children
        state_set = self.get_by_id('state_sets', state_set_id)
        if not state_set:
            return lambda: None
        children = set(state_set.get('states'))
        return clear_states

    def run(self):
        for button_type, button_id in self.get_button_presses():
            self.press_button(button_id, button_type=button_type)

    def get_button_presses(self):
        raise NotImplemented

class LircRiker(Riker):

    def __init__(self, lirc_name=None, **config):
        super(LircRiker, self).__init__(**config)
        self.lirc_name = lirc_name or 'riker'
        self.lircrc_filename = self.generate_lircrc_tempfile()
        print(self.lircrc_filename)

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

basic = {
    'buttons': [
        {
            'id': 123,
            'commands': [
                789,
                'poi',
            ],
            'lirc_code': 'POWER'
        },
    ],
    'active_states': [
        'abc',
    ],
    'conditions': [
        {
            'id': 456,
            'required_states': [
                'abc',
            ]
        }, 
        {
            'id': 'pl,',
            'required_states': [
                'zxc',
            ]
        },
    ],
    'commands': [
        {
            'id': 789,
            'type': 'fancy',
            'kwargs': {
                'thing1': 'val1',
                'thing2': 'val2',
            },
            'side_effects': [
                'zxc'
            ],
            'condition': 456,
        },
        {
            'id': 'poi',
            'type': 'fancy',
            'kwargs': {
                'thing1': 'otherval1',
                'thing2': 'otherval2',
            },
            'side_effects': [
                'abc'
            ],
            'condition': 'pl,',
        },
    ],
    'states': [
        {
            'id': 'zxc',
            'set': 'asd'
        },
        {
            'id': 'abc',
            'set': 'asd'
        }
    ],
    'state_sets': [
        {
            'id': 'asd',
            'states': [
                'zxc',
                'abc'
            ]
        }
    ]
}

test = LircRiker(**basic)
test.press_button('POWER')
print(test.active_states)
test.press_button('POWER')
print(test.active_states)
test.press_button('POWER')
print(test.active_states)
test.press_button('POWER')
print(test.active_states)
test.press_button('POWER')
print(test.buttons)
