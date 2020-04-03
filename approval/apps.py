from django.apps import AppConfig


class ApprovalConfig(AppConfig):
    name = 'approval'
    def ready(self):
        print("approval signals readsy")
        import approval.signals
