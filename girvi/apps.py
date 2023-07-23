from django.apps import AppConfig


class GirviConfig(AppConfig):
    # default_auto_field = 'django.db.models.BigAutoField'
    name = "girvi"

    def ready(self):
        import girvi.signals
