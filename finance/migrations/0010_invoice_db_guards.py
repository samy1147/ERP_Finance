# finance/migrations/0010_invoice_db_guards.py
# SQLite-compatible version
# PostgreSQL triggers would provide additional database-level validation,
# but for SQLite we rely on application-level validation in models and services.

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0009_taxcode_invoice_invoiceline_and_more"),
    ]

    operations = [
        # Add check constraint for non-negative totals (works on both SQLite and PostgreSQL)
        migrations.AddConstraint(
            model_name="invoice",
            constraint=models.CheckConstraint(
                name="ck_invoice_totals_nonnegative",
                check=models.Q(total_net__gte=0) & models.Q(total_tax__gte=0) & models.Q(total_gross__gte=0),
            ),
        ),
        
        # Create unique index for reversal_ref_id (SQLite compatible)
        # This ensures only one reversal per original invoice
        migrations.RunSQL(
            sql="""
                CREATE UNIQUE INDEX IF NOT EXISTS uq_invoice_reversal_ref
                ON finance_invoice (reversal_ref_id)
                WHERE reversal_ref_id IS NOT NULL;
            """,
            reverse_sql="DROP INDEX IF EXISTS uq_invoice_reversal_ref;",
        ),
    ]


# ==============================================================================
# NOTE FOR POSTGRESQL USERS:
# ==============================================================================
# If you're using PostgreSQL instead of SQLite, you can enable additional
# database-level validation by uncommenting and adding these operations:
#
# PostgreSQL-specific triggers would enforce:
# 1. Block posting if invoice has no lines
# 2. Block posting if any line is missing account or tax
# 3. Block posting if totals are zero
# 4. Normalize header totals to match line sums at posting time
# 5. Make posted invoices read-only (except status, reversal_ref, timestamps)
#
# To enable PostgreSQL triggers, see the original migration in:
# finance_invoice_validation_pack/migrations/00xx_invoice_db_guards.py
#
# For SQLite, these validations are handled in:
# - finance.models.Invoice.clean() method
# - finance.services.post_invoice() function
# ==============================================================================
