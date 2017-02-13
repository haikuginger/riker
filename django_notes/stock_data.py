# Create a TV to control
tv = Device.objects.create(name='Living Room TV')

# Create a remote button for power
power_button = RemoteButton.objects.create(lirc_code='BUTTON_POWER')

# Indicate that the state of the TV's power can change
tv_power_state = StateCategory.objects.create(
    name='TV power',
    device=tv
)

# Indicate that the TV can be powered on...
power_on_state = State.objects.create(
    name='Powered on',
    state_category=tv_power_state
)

# ... or powered off.
power_off_state = State.objects.create(
    name='Powered off',
    state_category=tv_power_state
)

# Set the status of the TV to off.
tv_power_state.status = power_off_state

# Create a power on command that happens when the power button is pressed. Condition it on
# happening only when the TV is in a power-off state.
power_on = BaseCommand.objects.create(
    device=tv,
    trigger=power_button,
    command_type='cec',
    data='whatever',
    condition=power_off_state
)

# Indicate that as a side effect of calling the power-on command, the state of the TV
# changes from being off to being on.
power_on_side_effect = StateSideEffect.objects.create(
    command=power_on,
    state=power_on_state
)

# Create a power off command that happens when the power button is pressed. Condition it on
# happening only when the TV is in a power-on state.
power_off = BaseCommand.objects.create(
    device=tv,
    trigger=power_button,
    command_type='cec',
    data='whatever',
    condition=power_on_state
)

# Indicate that as a side effect of calling the power-off command, the state of the TV
# changes from being on to being off.
power_on_side_effect = StateSideEffect.objects.create(
    command=power_off,
    state=power_off_state
)

# Trigger the button. Because the TV is currently in a power-off state, the power-on
# command will be executed, and then the state will be transitioned to power-on.
power_button.execute()
