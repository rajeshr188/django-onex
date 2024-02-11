from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "users"

    def ready(self):
        from actstream import registry

        import users.signals

        registry.register(self.get_model("CustomUser"))
