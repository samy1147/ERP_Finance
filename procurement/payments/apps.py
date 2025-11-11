from django.apps import AppConfig


class PaymentIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'procurement.payments'
    verbose_name = 'Procurement Payments'
