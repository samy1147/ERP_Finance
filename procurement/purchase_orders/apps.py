from django.apps import AppConfig


class PoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'procurement.purchase_orders'
    verbose_name = 'Purchase Orders'
