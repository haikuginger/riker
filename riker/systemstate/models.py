from logging import getLogger

from django.db import models


LOGGER = getLogger(__name__)


class RemoteButton(models.Model):

    lirc_code = models.CharField(
        unique=True,
        max_length=255,
    )

    def execute(self):
        effects = []
        for command in self.commands.all():
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
        'RemoteButton',
        related_name='commands'
    )
    command_type = models.CharField(
        max_length=255,
    )
    data = models.CharField(
        null=True,
        blank=True,
        max_length=255,
    )
    condition = models.ForeignKey(
        'State',
        related_name='+',
        null=True,
        blank=True,
    )

    def execute(self):
        handler = self.device.get_handler(self.command_type)
        if not self.condition or self.condition.is_active():
            handler(self.data)
            return list(self.side_effects.all())
    
    def __repr__(self):
        return '{} command {} triggered by {}'.format(self.command_type, self.data, self.trigger)

    def __str__(self):
        return self.__repr__()


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
    command = models.ForeignKey(
        'Command',
        related_name='side_effects',
    )
    state = models.ForeignKey(
        'State',
        related_name='reachable_by'
    )

    def execute(self):
        self.state.activate()

    def __repr__(self):
        return 'Set {} to {} after {}'.format(self.state.state_set, self.state, self.command)

    def __str__(self):
        return self.__repr__()

class Device(models.Model):

    command_types = {
        'cec': 'cec_config',
        'tcp': 'tcp_config',
        'serial': 'serial_config',
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
