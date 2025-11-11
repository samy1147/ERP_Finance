from django.apps import AppConfig


class RequisitionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'procurement.requisitions'
    label = 'requisitions'
    verbose_name = 'Purchase Requisitions'
