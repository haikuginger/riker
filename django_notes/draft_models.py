class RemoteButton(object):
    lirc_code = 'CharField(unique=True)'

    def execute(self):
        effects = []
        for command in self.command_set.all():
            side_effects = command.execute()
            if side_effects:
                effects += side_effects
        for effect in effects:
            effect.execute()

class BaseCommand(object):
    device = 'ForeignKey:Device'
    trigger = 'ForeignKey:RemoteButton'
    command_type = 'ChoiceField'
    data = 'CharField'
    condition = 'ForeignKey:State(null=True)'

    def execute(self):
        handler = self.device.get_handler(self.command_type)
        if not self.condition or self.condition.is_active():
            handler(self.data)
            return list(self.state_side_effect_set.all())


class StateCategory(object):
    name = 'CharField'
    status = 'ForeignKey:State'
    device = 'ForeignKey:Device'

class State(object):
    name = 'CharField'
    state_category = 'ForeignKey:StateCategory'

    def is_active(self):
        return self == self.state_category.status

    def activate(self):
        self.state_category.status = self

class StateSideEffect(object):
    command = 'ForeignKey:BaseCommand'
    state = 'ForeignKey:State'

    def execute(self):
        self.state.activate()

class Device(object):

    command_types = {
        'cec': 'cec_config',
        'tcp': 'tcp_config',
        'serial': 'serial_config',
    }

    name = 'CharField'
    cec_config = 'OneToOneField:CecConfig'
    tcp_config = 'OneToOneField:TcpConfig'
    serial_config = 'OneToOneField:SerialConfig'

    def get_handler(self, command_type):
        return getattr(self, self.command_types[command_type]).handler

class CecConfig(object):

    source_address = 'PositiveIntegerField'
    target_address = 'PositiveIntegerField'

    def handler(self):
        pass

class SerialConfig(object):

    port_name = 'CharField'
    baud_rate = 'PositiveIntegerField'
    byte_size = 'PositiveIntegerField'
    timeout = 'PositiveIntegerField'

    def handler(self):
        pass

class TcpConfig(object):

    ip_address = 'CharField'
    port = 'PositiveIntegerField'

    def handler(self):
        pass
