from django.apps import AppConfig



class SamalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'samal'
    verbose_name = "Онлайн продажи Samal"

    def ready(self):
        import samal.signals