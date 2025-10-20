# finance/apps.py
from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "finance"
    
    def ready(self):
        """Import signal handlers when Django starts"""
        try:
            import finance.signals  # noqa: F401
        except ImportError as e:
            raise RuntimeError(
                f"Failed to import finance.signals. "
                f"Check that finance/signals.py exists and has no syntax errors: {e}"
            )
