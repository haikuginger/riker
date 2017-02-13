from __future__ import unicode_literals

from django.apps import AppConfig

from worker.utils import LircListener


class WorkerConfig(AppConfig):
    name = 'worker'

    def ready(self):
        lirc_name = getattr(settings, 'RIKER_LIRC_LISTENER_NAME', 'riker')
        LircListener(lirc_name=lirc_name).start()
