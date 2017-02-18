from logging import getLogger

from systemstate.models import RemoteButton

LOGGER = getLogger(__name__)

def push_button(code):
    try:
        button = RemoteButton.objects.get(lirc_code=code)
    except RemoteButton.DoesNotExist:
        LOGGER.warning('Did not find handler for remote button with code {}.'.format(code))
    else:
        LOGGER.warning('Executing command for button: {}'.format(button))
        button.execute()
