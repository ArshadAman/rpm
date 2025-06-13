from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rpm_users'
    
    def ready(self):
        import rpm_users.signals
