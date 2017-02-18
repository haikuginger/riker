from django.contrib import admin
from systemstate.models import (
    RemoteButton,
    Command,
    CommandSet,
    Condition,
    StateSet,
    State,
    StateSideEffect,
    Device,
    IrsendConfig,
    CecConfig,
    SerialConfig,
    TcpConfig,
)

@admin.register(RemoteButton)
class RemoteButtonAdmin(admin.ModelAdmin):
    pass


@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    pass

class InlineCommandAdmin(admin.StackedInline):
    model = Command

@admin.register(CommandSet)
class CommandSetAdmin(admin.ModelAdmin):
    inlines = [
        InlineCommandAdmin
    ]

@admin.register(Condition)
class ConditionAdmin(admin.ModelAdmin):
    pass

class InlineStateAdmin(admin.StackedInline):
    model = State

@admin.register(StateSet)
class StateSetAdmin(admin.ModelAdmin):
    inlines = [
        InlineStateAdmin,
    ]

@admin.register(IrsendConfig)
class IrsendConfigAdmin(admin.ModelAdmin):
    pass


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    pass


@admin.register(StateSideEffect)
class StateSideEffectAdmin(admin.ModelAdmin):
    pass


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    pass


@admin.register(CecConfig)
class CecConfigAdmin(admin.ModelAdmin):
    pass


@admin.register(SerialConfig)
class SerialConfigAdmin(admin.ModelAdmin):
    pass


@admin.register(TcpConfig)
class TcpConfigAdmin(admin.ModelAdmin):
    pass
