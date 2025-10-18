from django.core.management.base import BaseCommand
from backend_app.scripts.import_clean_data import import_users, import_books, import_ratings
import os

class Command(BaseCommand):
    help = "Import users, books, and ratings from clean_data CSVs"

    def handle(self, *args, **options):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # go up 3 levels: backend_app/management/commands → backend_app
        DATA_DIR = os.path.join(BASE_DIR, '..', '..', 'clean_data')
        import_users(os.path.join(DATA_DIR, 'users.csv'))
        import_books(os.path.join(DATA_DIR, 'books.csv'))
        import_ratings(os.path.join(DATA_DIR, 'ratings.csv'))
        self.stdout.write(self.style.SUCCESS("✅ Data imported successfully!"))
