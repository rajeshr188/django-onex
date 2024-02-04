from django.apps import AppConfig


class GirviConfig(AppConfig):
    # default_auto_field = 'django.db.models.BigAutoField'
    name = "girvi"

    def ready(self):
        from actstream import registry
        registry.register(self.get_model('Loan'))
        registry.register(self.get_model('License'))
        registry.register(self.get_model('Series'))
        registry.register(self.get_model('LoanItem'))
        registry.register(self.get_model('Adjustment'))
        registry.register(self.get_model('Release'))
        import girvi.signals
