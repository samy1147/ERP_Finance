from django.apps import AppConfig


class PeriodsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'periods'
    verbose_name = 'Fiscal Periods Management'

    def ready(self):
        """Import signals when app is ready"""
        try:
            import periods.signals  # noqa
        except ImportError:
            pass
