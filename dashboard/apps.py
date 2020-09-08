from django.apps import AppConfig
from sales.models import Invoice
from girvi.models import Loan
from contact.models import Customer

class DashboardConfig(AppConfig):
    name = 'dashboard'

    def ready(self):
        from actstream import registry
        # registry.register(self.get_model('MyModel'))
        registry.register(self.get_model('Loan'))
        registry.register(self.get_model('Customer'))
