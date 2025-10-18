import csv
from django.db import transaction
from backend_app.models import User, Book, Rating


@transaction.atomic
def import_users(file_path):
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        users = []
        for row in reader:
            raw_age = row.get('age', '').strip()
            if raw_age:
                try:
                    age = int(float(raw_age))  # handle '18.0', '20.5', etc.
                except ValueError:
                    age = None
            else:
                age = None

            users.append(User(
                user_id=row['user_id'],
                age=age,
                location=row.get('location') or ''
            ))
        User.objects.bulk_create(users, ignore_conflicts=True)
    print(f"✅ Imported {len(users)} users.")

@transaction.atomic
def import_books(file_path):
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        books = []
        for row in reader:
            # Handle missing or malformed year safely
            raw_year = row.get('year_of_publication', '').strip()
            try:
                year = int(float(raw_year)) if raw_year else None
            except ValueError:
                year = None

            books.append(Book(
                book_isbn=row['book_isbn'],
                book_title=row.get('book_title', '')[:255],
                book_author=row.get('book_author', '')[:255],
                year_of_publication=year,
                publisher=row.get('publisher', '')[:255],
                image_url_s=row.get('image_url_s', '')[:500],
                image_url_m=row.get('image_url_m', '')[:500],
                image_url_l=row.get('image_url_l', '')[:500],
            ))

        Book.objects.bulk_create(books, ignore_conflicts=True)
    print(f"✅ Imported {len(books)} books.")


@transaction.atomic
def import_ratings(file_path):
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        ratings = []
        total = 0

        # Normalize header names to lowercase for safety
        field_map = {name.lower(): name for name in reader.fieldnames}
        user_col = field_map.get('user_id') or field_map.get('user-id')
        book_col = field_map.get('book_isbn') or field_map.get('isbn')
        rating_col = (
            field_map.get('rating')
            or field_map.get('book_rating')
            or field_map.get('book-rating')
        )

        if not all([user_col, book_col, rating_col]):
            raise ValueError(f"❌ Missing required columns in CSV. Found: {reader.fieldnames}")

        # Pre-fetch IDs to avoid ORM lookups
        user_map = {u.user_id: u.id for u in User.objects.all().only("id", "user_id")}
        book_map = {b.book_isbn: b.id for b in Book.objects.all().only("id", "book_isbn")}

        for row in reader:
            total += 1
            user_id = str(row[user_col]).strip()
            book_isbn = str(row[book_col]).strip()
            raw_rating = row[rating_col].strip()

            if not user_id or not book_isbn or not raw_rating:
                continue

            try:
                rating_value = float(raw_rating)
            except ValueError:
                continue

            # Directly use IDs — skip DB fetch
            user_fk = user_map.get(user_id)
            book_fk = book_map.get(book_isbn)
            if user_fk and book_fk:
                ratings.append(Rating(user_id=user_fk, book_id=book_fk, rating=rating_value))

            # Bulk insert every 50,000 rows (larger batch for performance)
            if len(ratings) >= 50000:
                Rating.objects.bulk_create(ratings, ignore_conflicts=True)
                ratings.clear()

        # Final insert
        if ratings:
            Rating.objects.bulk_create(ratings, ignore_conflicts=True)

    print(f"✅ Imported {total} ratings from {file_path}")

