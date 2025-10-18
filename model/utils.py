import torch
from collections import defaultdict, deque
from django.db import transaction
from .models import User, Book, Rating

# ----------------------------------------------------------------
# GLOBALS (cache-like structures, not DB)
# ----------------------------------------------------------------
user_sequences = defaultdict(lambda: deque(maxlen=10))  # keep short-term interactions
book_index = {}
index_book = {}
user_index = {}
index_user = {}
trained_model = None
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ----------------------------------------------------------------
# MODEL + MAPPING INITIALIZATION
# ----------------------------------------------------------------
def load_model(model_path, model_class):
    """Load trained STAMP model into memory."""
    global trained_model
    trained_model = model_class()
    trained_model.load_state_dict(torch.load(model_path, map_location=device))
    trained_model.to(device)
    trained_model.eval()
    print("✅ STAMP model loaded successfully.")


def load_mappings_from_db():
    """Create index mappings directly from SQL tables."""
    global book_index, index_book, user_index, index_user

    books = Book.objects.all().values_list("book_isbn", flat=True)
    users = User.objects.all().values_list("user_id", flat=True)

    book_index = {isbn: idx for idx, isbn in enumerate(books)}
    index_book = {idx: isbn for isbn, idx in book_index.items()}
    user_index = {uid: idx for idx, uid in enumerate(users)}
    index_user = {idx: uid for uid, idx in user_index.items()}

    print(f"✅ Loaded mappings → {len(users)} users, {len(books)} books")


# ----------------------------------------------------------------
# INTERACTION FUNCTIONS
# ----------------------------------------------------------------
def record_interaction(user_id, book_isbn, rating=None):
    """
    Record a user-book interaction.
    Automatically updates both Django DB and in-memory cache.
    """
    # Ensure user and book exist in DB
    user, _ = User.objects.get_or_create(user_id=user_id)
    book, _ = Book.objects.get_or_create(book_isbn=book_isbn)

    # Save interaction to DB
    if rating is not None:
        Rating.objects.update_or_create(user=user, book=book, defaults={"rating": rating})

    # Update in-memory sequence
    user_sequences[user_id].append(book_isbn)
    return {"status": "ok", "message": f"Interaction recorded for user {user_id}"}


def recommend_books(user_id, top_k=5):
    """Generate top-k book recommendations for given user."""
    if trained_model is None:
        raise ValueError("Model not loaded. Call load_model first.")

    # Cold start case
    seq = list(user_sequences[user_id])
    if not seq:
        books = list(Book.objects.values_list("book_isbn", flat=True))
        if not books:
            return {"user_id": user_id, "recommendations": []}
        return {
            "user_id": user_id,
            "recommendations": list(set(books))[:top_k]
        }

    # Convert seq to tensor indices
    seq_idx = [book_index[b] for b in seq if b in book_index]
    if not seq_idx:
        return {"user_id": user_id, "recommendations": []}

    seq_tensor = torch.tensor(seq_idx).unsqueeze(0).to(device)

    with torch.no_grad():
        scores = trained_model(seq_tensor)
        top_indices = torch.topk(scores, top_k).indices.squeeze(0).tolist()

    rec_books = [index_book[i] for i in top_indices if i in index_book]
    return {"user_id": user_id, "recommendations": rec_books}


# ----------------------------------------------------------------
# NEW ENTRIES HANDLERS
# ----------------------------------------------------------------
@transaction.atomic
def handle_new_user(user_id, age=None, location=None):
    """Add new user to DB + initialize cache sequence."""
    user, created = User.objects.get_or_create(
        user_id=user_id,
        defaults={"age": age, "location": location}
    )
    user_sequences[user_id] = deque(maxlen=10)
    if created:
        # add to mapping
        new_idx = len(user_index)
        user_index[user_id] = new_idx
        index_user[new_idx] = user_id
    return {"status": "ok", "message": f"New user {user_id} {'created' if created else 'already exists'}."}


@transaction.atomic
def handle_new_book(book_isbn, title=None, author=None, genre=None):
    """Add new book to DB + update in-memory mapping."""
    book, created = Book.objects.get_or_create(
        book_isbn=book_isbn,
        defaults={"title": title or "", "author": author or "", "genre": genre or ""}
    )
    if created:
        new_idx = len(book_index)
        book_index[book_isbn] = new_idx
        index_book[new_idx] = book_isbn
    return {"status": "ok", "message": f"Book {book_isbn} {'added' if created else 'already exists'}."}
