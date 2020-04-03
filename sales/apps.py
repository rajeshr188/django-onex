from django.apps import AppConfig


class SalesConfig(AppConfig):
    name = 'sales'
    def ready(self):
        import sales.signals
