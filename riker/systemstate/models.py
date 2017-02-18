from logging import getLogger

from django.db import models

from commands.utils import(
    send_cec_command,
    send_infrared_command,
    send_serial_command,
    send_tcp_command,
)

LOGGER = getLogger(__name__)


class RemoteButton(models.Model):

    lirc_code = models.CharField(
        unique=True,
        max_length=255,
    )

    def execute(self):
        effects = []
        LOGGER.warning('Executing macros: {}'.format(self.macros.all()))
        for command in self.macros.all():
            side_effects = command.execute()
            if side_effects is not None:
                effects += side_effects
        for effect in effects:
            effect.execute()

    def __repr__(self):
        return self.lirc_code

    def __str__(self):
        return self.__repr__()


class Command(models.Model):
    device = models.ForeignKey(
        'Device',
        related_name='commands'
    )
    trigger = models.ForeignKey(
        'CommandSet',
        related_name='commands'
    )
    command_type = models.CharField(
        max_length=255,
    )
    condition = models.ForeignKey(
        'Condition',
        related_name='+',
        null=True,
        blank=True,
    )
    data = models.CharField(
        null=True,
        blank=True,
        max_length=255,
    )

    def execute(self):
        handler = self.device.get_handler(self.command_type)
        if not self.condition or self.condition.met():
            handler(self.data)

    def __repr__(self):
        return '{} command {} triggered by {}'.format(self.command_type, self.data, self.trigger)

    def __str__(self):
        return self.__repr__()


class CommandSet(models.Model):

    name = models.CharField(max_length=255)

    trigger = models.ForeignKey(
        'RemoteButton',
        related_name='macros'
    )

    condition = models.ForeignKey(
        'Condition',
        related_name='+',
        null=True,
        blank=True,
    )

    def execute(self):
        if hasattr(self, 'condition') and not self.condition.met():
            LOGGER.warning('Conditions for {} were not met.'.format(self))
            return None
        for command in self.commands.all():
            LOGGER.warning('Conditions for {} were met. Executing command {}.'.format(self, command))
            command.execute()
        return list(self.side_effects.all())

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.__repr__()


class Condition(models.Model):

    CONDITION_TYPES = [
        ('any', 'Any'),
        ('all', 'All'),
    ]

    condition_type = models.CharField(max_length=3, choices=CONDITION_TYPES)
    states = models.ManyToManyField('State', related_name='+', blank=True)
    nested_conditions = models.ManyToManyField('self',
        related_name='+',
        symmetrical=False,
        blank=True
    )

    def met(self):
        if self.condition_type == 'any':
            check_method = any
        else:
            check_method = all
        states_met = check_method(x.is_active() for x in self.states.all())
        nested_conditions_met = check_method(x.met() for x in self.nested_conditions.all())
        return check_method([states_met, nested_conditions_met])


class StateSet(models.Model):
    name = models.CharField(max_length=255)
    status = models.OneToOneField(
        'State',
        null=True,
        blank=True,
    )
    device = models.ForeignKey(
        'Device',
        related_name='state_sets'
    )

    def __repr__(self):
        return '{}: {}'.format(self.name, self.status)

    def __str__(self):
        return self.__repr__()


class State(models.Model):
    name = models.CharField(max_length=255)
    state_set = models.ForeignKey(
        'StateSet',
    )

    def is_active(self):
        return self == self.state_set.status

    def activate(self):
        self.state_set.status = self
        self.state_set.save()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.__repr__()


class StateSideEffect(models.Model):
    commands = models.ForeignKey(
        'CommandSet',
        related_name='side_effects',
    )
    states = models.ManyToManyField(
        'State',
        related_name='reachable_by'
    )

    def execute(self):
        for state in self.states.all():
            state.activate()

    def __repr__(self):
        return 'Set {} after {}'.format(', '.join(self.states.all()), self.commands)

    def __str__(self):
        return self.__repr__()

class Device(models.Model):

    command_types = {
        'cec': 'cec_config',
        'tcp': 'tcp_config',
        'serial': 'serial_config',
        'infrared': 'irsend_config',
    }

    name = models.CharField(
        max_length=255
    )
    cec_config = models.OneToOneField(
        'CecConfig',
        null=True,
        blank=True,
    )
    tcp_config = models.OneToOneField(
        'TcpConfig',
        null=True,
        blank=True,
    )
    serial_config = models.OneToOneField(
        'SerialConfig',
        null=True,
        blank=True,
    )
    irsend_config = models.OneToOneField(
        'IrsendConfig',
        null=True,
        blank=True,
    )

    def get_handler(self, command_type):
        return getattr(self, self.command_types[command_type]).handler

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.__repr__()


class CecConfig(models.Model):

    source_address = models.PositiveIntegerField()
    target_address = models.PositiveIntegerField()

    def handler(self, command):
        LOGGER.warning(
            'Sending CEC command {} from {} to {}.'.format(
                command,
                self.source_address,
                self.target_address,
            )
        )
        send_cec_command(
            source_address,
            target_address,
            command,
        )

    def __repr__(self):
        return 'CEC config' +  (' for {}'.format(self.device) if hasattr(self, 'device') else '')

    def __str__(self):
        return self.__repr__()


class SerialConfig(models.Model):

    port_name = models.CharField(max_length=255)
    baud_rate = models.PositiveIntegerField()
    byte_size = models.PositiveIntegerField()
    timeout = models.PositiveIntegerField()

    def handler(self, command):
        LOGGER.warning(
            'Sending serial command "{}" on port {} with byte size {}, baud rate {}, and timeout {}.'.format(
                command,
                self.port_name,
                self.byte_size,
                self.baud_rate,
                self.timeout,
            )
        )
        send_serial_command(
            self.port_name,
            self.baud_rate,
            self.byte_size,
            self.timeout,
            command,
        )

    def __repr__(self):
        return 'Serial config' +  (' for {}'.format(self.device) if hasattr(self, 'device') else '')

    def __str__(self):
        return self.__repr__()


class TcpConfig(models.Model):

    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField()

    def handler(self, command):
        LOGGER.warning(
            'Sending TCP command "{}" to host {} on port number {}.'.format(
                command,
                self.host,
                self.port,
            )
        )
        send_tcp_command(host, port, command)

    def __repr__(self):
        return 'TCP config' +  (' for {}'.format(self.device) if hasattr(self, 'device') else '')

    def __str__(self):
        return self.__repr__()


class IrsendConfig(models.Model):

    remote_name = models.CharField(max_length=255)

    def handler(self, command):
        LOGGER.warning(
            'Sending IR command "{}" with remote "{}".'.format(command, self.remote_name)
        )
        send_infrared_command(self.remote_name, command)

    def __repr__(self):
        return 'Infrared config' +  (' for {}'.format(self.device) if hasattr(self, 'device') else '')

    def __str__(self):
        return self.__repr__()
