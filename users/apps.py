from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "users"

    def ready(self):
        import users.signals
        from actstream import registry
        registry.register(self.get_model('CustomUser'))
