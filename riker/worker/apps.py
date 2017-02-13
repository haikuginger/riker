from __future__ import unicode_literals

from django.apps import AppConfig

from worker.utils import LircListener


class WorkerConfig(AppConfig):
    name = 'worker'
