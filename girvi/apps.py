from django.apps import AppConfig

class GirviConfig(AppConfig):
    name = 'girvi'

    def ready(self):
        import girvi.signals
        from actstream import registry
        registry.register(self.get_model('Loan'))
