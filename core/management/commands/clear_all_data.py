"""
Management command to clear all data from the database
Usage: python manage.py clear_all_data
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Delete all records from the database (keeps structure, removes data)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  WARNING: This will DELETE ALL DATA from the database!\n'
                    'This action cannot be undone.\n\n'
                    'To proceed, run:\n'
                    '  python manage.py clear_all_data --confirm\n'
                )
            )
            return

        self.stdout.write(self.style.WARNING('\n🗑️  Starting database cleanup...\n'))

        # Use raw SQL to delete all data (bypassing Django ORM and history tracking)
        with connection.cursor() as cursor:
            # Disable foreign key constraints temporarily
            cursor.execute("PRAGMA foreign_keys = OFF;")
            
            # Get all table names except Django system tables
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name NOT LIKE 'sqlite_%'
                AND name NOT LIKE 'django_%'
                AND name NOT LIKE 'auth_%'
                AND name NOT LIKE 'simple_history_%'
            """)
            tables = cursor.fetchall()
            
            total_deleted = 0
            
            # Delete all data from each table
            for (table_name,) in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        cursor.execute(f"DELETE FROM {table_name}")
                        total_deleted += count
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Deleted {count} records from {table_name}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'  - No data in {table_name}')
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Error deleting from {table_name}: {e}')
                    )

        # Reset auto-increment counters (SQLite)
        with connection.cursor() as cursor:
            # Get all table names
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name NOT LIKE 'sqlite_%'
                AND name NOT LIKE 'django_%'
                AND name NOT LIKE 'auth_%'
            """)
            tables = cursor.fetchall()
            
            for (table_name,) in tables:
                try:
                    cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
                except Exception:
                    pass  # Table might not have auto-increment

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully deleted {total_deleted} records!\n'
                'Database structure preserved, all data removed.\n'
            )
        )
