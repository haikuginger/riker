from riker.core import BaseRiker
from riker.config_parsers import JsonConfigParserMixin
from riker.input_handlers import LircInputHandlerMixin
from riker.command_handlers import (
    CecMixin,
    InfraredMixin,
    SerialMixin,
    TcpMixin
)

class BaseCommandTypesMixin(CecMixin, InfraredMixin, SerialMixin, TcpMixin):
    pass

class Riker(JsonConfigParserMixin, LircInputHandlerMixin, BaseCommandTypesMixin, BaseRiker):
    pass
