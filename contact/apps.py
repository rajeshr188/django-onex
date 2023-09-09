from django.apps import AppConfig


class ContactConfig(AppConfig):
    name = "contact"

    def ready(self):
        import contact.signals

        # from actstream import registry
        # registry.register(self.get_model('Customer'))
        # registry.register(self.get_model('Contact'))
        # registry.register(self.get_model('Address'))
