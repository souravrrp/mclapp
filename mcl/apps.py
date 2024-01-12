from django.apps import AppConfig


class MclConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mcl'

    def ready(self):
        import mcl.signals
