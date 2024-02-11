from django.apps import AppConfig


class ContactConfig(AppConfig):
    name = "contact"

    def ready(self):
        from actstream import registry

        import contact.signals

        registry.register(self.get_model("Customer"))
        registry.register(self.get_model("Contact"))
        registry.register(self.get_model("Address"))
