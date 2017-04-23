import json

class JsonConfigParserMixin(object):

    def __init__(self, config_file_name='riker_config.json', state_file_name='riker_state.json'):
        config = self.get_json_config(config_file_name)
        state = self.get_json_config(state_file_name)
        state = state['active_states']
        config.update(active_states=state)
        super(JsonConfigParserMixin, self).__init__(**config)

    def get_json_config(self, filename):
        try:
            with open(filename, 'r') as configfile:
                return json.load(configfile)
        except Exception:
            return {}