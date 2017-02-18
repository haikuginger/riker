from logging import getLogger

from django.core.management.base import BaseCommand, CommandError

from worker.utils import listen, create_lircrc_tempfile


LOGGER = getLogger(__name__)

class Command(BaseCommand):

    def handle(*args, **options):
        name = 'riker'
        fname = create_lircrc_tempfile(name)
        LOGGER.warning(
            'Created lircrc file at {}; starting to listen.'.format(
                fname
            )
        )
        listen(name, fname)
