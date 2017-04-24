# Devices
#     What is it called?
#         - Check command types
#         - Get config for each command type
#             - Treat input as JSON?

# State sets
#     What states can this set be in?

# Commands
#     What do you want to do?
#     What sort of command does that take?
#     What parameters need to be passed to that command?
#         - Input as JSON
#     What needs to be the case for this command to happen?
#         - Loop, getting individual states, eliminating contradictory states
#     What state changes happen as a result of this command?
#         - Loop, as above.

# Buttons:
#     What is this button called?
#     What type of button is it?
#     What is its identifier for that type?

import json
from copy import deepcopy
from uuid import uuid4

try:
    input = raw_input
except NameError:
    pass

COMMAND_TYPES = {
    'CEC': 'cec',
    'Infrared': 'infrared',
    'Serial': 'serial',
    'TCP': 'tcp',
}

BUTTON_TYPES = {
    'Lirc': 'lirc'
}

class InterruptedConfig(Exception):

    def __init__(self, *args, **kwargs):
        self.incomplete_config = kwargs.pop('incomplete_config', {})
        super(InterruptedConfig, self).__init__(*args, **kwargs)


def new_item(name):
    return {
        "name": name,
        "id": uuid4().hex
    }

def pick_one(message, items, return_quickly=True, require=False):
    if isinstance(items, dict):
        items = [{'name': key, 'id': value} for key, value in items.items()]
    items = list(items)
    if len(items) == 1 and return_quickly:
        return items[0]
    print(message)
    choice = input('\n'.join('{}. {}'.format(i+1, item['name']) for i, item in enumerate(items)) + '\n')
    if not choice and not require:
        return None
    elif not choice:
        return pick_one(message, items, return_quickly=return_quickly, require=require)
    choice = int(choice) - 1
    return items[choice]

def pick_compatible_states(message, state_sets, states):
    state_sets = deepcopy(state_sets)
    states = deepcopy(states)
    chosen_states = []
    while True and states:
        state_choice = pick_one(message, states)
        if not state_choice:
            break
        chosen_states.append(state_choice)
        set_to_remove = next(x for x in state_sets if x['id'] == state_choice['set'])
        states = [x for x in states if x['id'] not in set_to_remove['states']]
    return chosen_states

def pick_many(message, items):
    picked = []
    while True and items:
        item = pick_one(message, items, return_quickly=False)
        if not item:
            break
        picked.append(item)
        items = [x for x in items if x != item]
    return picked

def get_devices():
    devices = []
    while True:
        device_name = input('Do you have another device? What is its name? ')
        if not device_name:
            break
        device = new_item(device_name)
        for human_type, cmd_type in COMMAND_TYPES.items():
            config = input('Does it have a {} configuration? '.format(human_type))
            if config:
                config = json.loads(config)
                device[cmd_type] = config
        devices.append(device)
    return devices

def get_states():
    states = []
    state_sets = []
    while True:
        set_name = input('What is the name of a set of mutually-exclusive states that exists in your system? ')
        if not set_name:
            break
        state_set = new_item(set_name)
        state_set['states'] = []
        while True:
            state_name = input('What is a name for one of the states in "{}"? '.format(set_name))
            if not state_name:
                break
            state = new_item(state_name)
            state['set'] = state_set['id']
            states.append(state)
            state_set['states'].append(state['id'])
        state_sets.append(state_set)
    return state_sets, states

def get_commands(devices, state_sets, states):
    commands = []
    conditions = []
    while True:
        command_name = input('What is the name of a command you need to perform? ')
        if not command_name:
            break
        command = new_item(command_name)
        prerequisites = pick_compatible_states(
            'What states must exist for this command to take effect?',
            state_sets,
            states,
        )
        condition_name = ' AND '.join(x['name'] for x in prerequisites)
        condition = new_item(condition_name)
        condition['required_states'] = [x['id'] for x in prerequisites]
        command['condition'] = condition['id']
        conditions.append(condition)
        command['device'] = pick_one('What device is it performed on?', devices, require=True)['id']
        command['type'] = pick_one('What type of command is it?', COMMAND_TYPES, require=True)['id']
        arguments = input("What necessary arguments are there? ")
        try:
            arguments = json.loads(arguments)
        except Exception:
            arguments = {"command": arguments}
        command['kwargs'] = arguments
        side_effects = pick_compatible_states(
            'What states happen as a result of this command?',
            state_sets,
            states,
        )
        command['side_effects'] = [x['id'] for x in side_effects]
        commands.append(command)
    return commands, conditions

def get_buttons(commands):
    buttons = []
    while True:
        button_name = input('What is the name of a button that might be pushed? ')
        if not button_name:
            break
        button = new_item(button_name)
        button['type'] = pick_one('What type of button is "{}"?'.format(button_name), BUTTON_TYPES, require=True)['id']
        button['code'] = input(
            'What code or ID does {} send the "{}" button with? '.format(
                button['type'],
                button_name
            )
        )
        chosen_commands = pick_many('What commands can the "{}" button send?'.format(button_name), commands)
        button['commands'] = [x['id'] for x in chosen_commands]
        buttons.append(button)
    return buttons

def update_child(config, child_name, to_update):
    config.setdefault(child_name, [])
    config[child_name] += to_update

def run(existing_config=None):
    config = existing_config.copy() or {}
    try:
        update_child(config, 'devices', get_devices())
        state_sets, states = get_states()
        update_child(config, 'state_sets', state_sets)
        update_child(config, 'states', states)
        commands, conditions = get_commands(
            config['devices'],
            config['state_sets'],
            config['states']
        )
        update_child(config, 'commands', commands)
        update_child(config, 'conditions', conditions)
        update_child(config, 'buttons', get_buttons(config['commands']))
        print(config)
        return config
    except:
        raise InterruptedConfig('Could not complete configuration', incomplete_config=config)

if __name__ == '__main__':
    try:
        with open('draft_config.json', 'r') as existing_config:
            config = json.load(existing_config)
            print('Successfully loaded draft configuration...')
    except Exception:
        config = {}

    try:
        final_config = run(config)
        with open('config.json', 'w') as configfile:
            configfile.write(json.dumps(final_config, indent=4))
    except InterruptedConfig as err:
        print('Configuration failed; dumping state...')
        with open('draft_config.json', 'w') as configfile:
            configfile.write(json.dumps(err.incomplete_config, indent=4))


