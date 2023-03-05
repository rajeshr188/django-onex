from django.apps import AppConfig


class ApprovalConfig(AppConfig):
    name = "approval"

    def ready(self):
        import approval.signals
