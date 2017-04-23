import json
import logging
import tempfile
import lirc
from functools import partial


LOGGER = logging.getLogger(__name__)

def all_return_true(functions):
    return all (x() for x in functions) if functions else True

def run_all(functions):
    cleanup = []
    for each in functions:
        if each is not None:
            cleanup.append(each())
    return cleanup


class BaseRiker(object):

    def __init__(self, **config):
        self.config = config
        self.active_states = set(self.config.get('active_states', []))
        self.buttons = {
            (button['type'], button['code']): self.process_button(button) for button in config.get('buttons', [])
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
                action()
                return lambda: run_all(side_effects)
        command = self.get_by_id('commands', command_id)
        if command is None:
            return lambda: None
        else:
            condition_check = self.get_condition_checker(command.get('condition'))
            side_effects = [self.get_state_setter(state) for state in command.get('side_effects', [])]
            action = self.get_action_for_command(command)
            return run_command

    def get_action_for_command(command):
        action_type = command['type']
        handler = self.command_handleers[action_type]
        device_config = self.get_device_config(command.get('device_id'), action_type)
        return partial(handler, *command.get('args', []), **command.get('kwargs', {}))

    def get_device_config(device_id, config_type):
        device = self.get_by_id('devices', device_id) or {}
        return device.get(config_type, {})

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
