from django.core.management.base import BaseCommand, CommandError

from worker.utils import listen, createlircrc_tempfile

class Command(BaseCommand):

    def handle(*args, **options):
        name = 'riker'
        fname = createlircrc_tempfile(name)
        listen(name, fname)