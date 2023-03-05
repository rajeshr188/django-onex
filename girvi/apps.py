from django.apps import AppConfig


class GirviConfig(AppConfig):
    name = "girvi"

    def ready(self):
        import girvi.signals
