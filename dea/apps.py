from django.apps import AppConfig


class DeaConfig(AppConfig):
    name = "dea"

    def ready(self):
        from . import signals
