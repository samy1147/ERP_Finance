# Generated manually to fix missing database columns
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fixed_assets', '0009_assettransfer_approval_status'),
    ]
    
    # Disable atomic to run outside transaction
    atomic = False

    operations = [
        migrations.RunSQL(
            sql=[
                # Each statement executed separately to avoid transaction issues
                "PRAGMA foreign_keys = OFF;",
            ],
            reverse_sql=["PRAGMA foreign_keys = ON;"],
        ),
        migrations.RunSQL(
            sql=["ALTER TABLE assets_asset ADD COLUMN capitalization_journal_id INTEGER NULL;"],
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=["ALTER TABLE assets_asset ADD COLUMN disposal_journal_id INTEGER NULL;"],
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=["ALTER TABLE assets_asset ADD COLUMN currency_id INTEGER NULL;"],
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=["ALTER TABLE assets_asset ADD COLUMN category_id INTEGER NULL;"],
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=["ALTER TABLE assets_asset ADD COLUMN created_by_id INTEGER NULL;"],
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=["ALTER TABLE assets_asset ADD COLUMN supplier_id INTEGER NULL;"],
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=["ALTER TABLE assets_asset ADD COLUMN depreciation_expense_account_id INTEGER NULL;"],
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=["ALTER TABLE assets_asset ADD COLUMN ap_invoice_id INTEGER NULL;"],
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=["ALTER TABLE assets_asset ADD COLUMN ap_invoice_line INTEGER NULL;"],
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=["ALTER TABLE assets_asset ADD COLUMN grn_id INTEGER NULL;"],
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=["ALTER TABLE assets_asset ADD COLUMN grn_line_id INTEGER NULL;"],
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=["ALTER TABLE assets_asset ADD COLUMN source_type VARCHAR(20) DEFAULT 'MANUAL';"],
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=["PRAGMA foreign_keys = ON;"],
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
