# Generated migration to set default payment_status for existing records

from django.db import migrations


def set_default_payment_status(apps, schema_editor):
    """Set payment_status to UNPAID for any records where it's NULL"""
    ARInvoice = apps.get_model('ar', 'ARInvoice')
    
    # Update any records with NULL payment_status
    updated = ARInvoice.objects.filter(payment_status__isnull=True).update(payment_status='UNPAID')
    
    if updated > 0:
        print(f"Updated {updated} AR invoices with NULL payment_status to UNPAID")


def reverse_migration(apps, schema_editor):
    """No reverse operation needed"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('ar', '0004_migrate_status_to_new_fields'),
    ]

    operations = [
        migrations.RunPython(set_default_payment_status, reverse_migration),
    ]
