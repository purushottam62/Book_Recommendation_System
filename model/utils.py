import os
import sys
import torch
import threading
from collections import defaultdict, deque
from django.db import transaction

# --------------------------------------------------------
# Django setup
# --------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
if not django.apps.apps.ready:
    django.setup()

from backend_app.models import User, Book, Rating


# --------------------------------------------------------
# GLOBAL STATE
# --------------------------------------------------------
_GLOBAL_STATE = {
    "trained_model": None,
    "book_index": {},
    "index_book": {},
    "user_index": {},
    "index_user": {},
}

# Each user's interaction sequence is stored independently
_user_sequences = defaultdict(lambda: deque(maxlen=20))
_sequence_locks = defaultdict(threading.Lock)
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --------------------------------------------------------
# MODEL LOADING FUNCTIONS
# --------------------------------------------------------
def load_model(model_path, model_class):
    """Load trained STAMP model and resize embeddings if DB size changed."""
    load_mappings_from_db()
    num_items = len(_GLOBAL_STATE["book_index"]) or Book.objects.count()
    if num_items == 0:
        raise ValueError("❌ No books found in DB — cannot initialize STAMP model.")

    # Initialize model
    model = model_class(num_items=num_items, embed_dim=64)
    checkpoint = torch.load(model_path, map_location=_device)

    # Handle mismatched layer shapes
    model_dict = model.state_dict()
    for key, value in checkpoint.items():
        if key in model_dict and value.shape != model_dict[key].shape:
            print(f"⚠️ Resizing {key}: {value.shape} → {model_dict[key].shape}")
            min_shape = tuple(min(a, b) for a, b in zip(value.shape, model_dict[key].shape))
            model_dict[key][:min_shape[0], ...] = value[:min_shape[0], ...]
        else:
            model_dict[key] = value

    model.load_state_dict(model_dict, strict=False)
    model.to(_device)
    model.eval()

    _GLOBAL_STATE["trained_model"] = model
    print(f"✅ STAMP model loaded successfully from: {model_path}")
    print(f"   → num_items = {num_items}, embed_dim = 64")



def load_mappings_from_db():
    """Load all users and books from DB into memory mappings."""
    books = list(Book.objects.values_list("book_isbn", flat=True))
    users = list(User.objects.values_list("user_id", flat=True))

    book_index = {isbn: idx for idx, isbn in enumerate(books)}
    index_book = {idx: isbn for isbn, idx in book_index.items()}
    user_index = {uid: idx for idx, uid in enumerate(users)}
    index_user = {idx: uid for uid, idx in user_index.items()}

    _GLOBAL_STATE.update({
        "book_index": book_index,
        "index_book": index_book,
        "user_index": user_index,
        "index_user": index_user,
    })

    print(f"✅ Loaded mappings → {len(users)} users, {len(books)} books")
# --------------------------------------------------------
# INTERACTION FUNCTIONS
# --------------------------------------------------------
def record_interaction(user_id, book_isbn, rating=None, implicit=False):
    """
    Record a user-book interaction safely (thread-safe + consistent per-user sequence).
    - Implicit=True means a neutral 'view' event.
    - Explicit rating always overrides implicit.
    - User sequences stored separately (no cross-contamination).
    """
    user, _ = User.objects.get_or_create(user_id=user_id)
    book, _ = Book.objects.get_or_create(book_isbn=book_isbn)

    existing = Rating.objects.filter(user=user, book=book).first()
    if implicit:
        if existing is None:
            Rating.objects.create(user=user, book=book, rating=7.14)
            msg = f"Implicit (view) rating recorded for {book_isbn}"
        else:
            msg = f"Skipped implicit rating — explicit already exists for {book_isbn}"
    else:
        Rating.objects.update_or_create(user=user, book=book, defaults={"rating": rating})
        msg = f"Explicit rating {rating} recorded for {book_isbn}"

    # Thread-safe session append
    with _sequence_locks[user_id]:
        _user_sequences[user_id].append(book_isbn)

    return {"status": "ok", "message": msg}

def recommend_books(user_id, top_k=5):
    """
    Generate top-k recommendations for a given user.
    Returns list of book_isbn recommendations.
    """
    model = _GLOBAL_STATE.get("trained_model")
    if model is None:
        raise ValueError("Model not loaded. Please check auto-load configuration.")

    book_index = _GLOBAL_STATE["book_index"]
    index_book = _GLOBAL_STATE["index_book"]

    # Retrieve this user's sequence safely
    with _sequence_locks[user_id]:
        seq = list(_user_sequences[user_id])

    if not seq:
        books = list(Book.objects.values_list("book_isbn", flat=True)[:top_k])
        return {"user_id": user_id, "recommendations": books}

    seq_idx = [book_index[b] for b in seq if b in book_index]
    if not seq_idx:
        return {"user_id": user_id, "recommendations": []}

    seq_tensor = torch.tensor([seq_idx], dtype=torch.long).to(_device)

    with torch.no_grad():
        scores = model(seq_tensor)  # full item scores
        scores = torch.softmax(scores, dim=-1)  # normalize
        top_indices = torch.topk(scores, top_k, dim=1).indices.squeeze(0).tolist()

    rec_books = [index_book[i] for i in top_indices if i in index_book]
    return {"user_id": user_id, "recommendations": rec_books}

# --------------------------------------------------------
# HANDLERS
# --------------------------------------------------------
@transaction.atomic
def handle_new_user(user_id, age=None, location=None):
    user, created = User.objects.get_or_create(
        user_id=user_id,
        defaults={"age": age, "location": location},
    )
    _user_sequences[user_id] = deque(maxlen=20)
    return {"status": "ok", "message": f"User {user_id} {'created' if created else 'exists'}."}


@transaction.atomic
def handle_new_book(book_isbn, book_title=None, book_author=None,
                    year_of_publication=None, publisher=None,
                    image_url_s=None, image_url_m=None, image_url_l=None):
    book, created = Book.objects.get_or_create(
        book_isbn=book_isbn,
        defaults={
            "book_title": book_title or "",
            "book_author": book_author or "",
            "year_of_publication": year_of_publication,
            "publisher": publisher or "",
            "image_url_s": image_url_s or "",
            "image_url_m": image_url_m or "",
            "image_url_l": image_url_l or "",
        },
    )
    return {"status": "ok", "message": f"Book {book_isbn} {'added' if created else 'exists'}."}

# --------------------------------------------------------
# THREADED AUTO-LOAD FUNCTION
# --------------------------------------------------------
def _auto_load_stamp_model_once():
    """Automatically load STAMP model and mappings after Django setup."""
    try:
        try:
            from model.stamp_model import STAMP
        except ModuleNotFoundError:
            from stamp_model import STAMP

        possible_paths = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "stamp.pth")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../model/stamp.pth")),
            os.path.abspath(os.path.join(os.getcwd(), "model/stamp.pth")),
        ]

        print("🔍 Checking possible STAMP model paths:")
        for p in possible_paths:
            print("   -", p)

        model_path = next((p for p in possible_paths if os.path.exists(p)), None)
        if model_path is None:
            print("⚠️ No valid stamp.pth found in any known path!")
            return

        print(f"✅ Found model file at: {model_path}")
        load_model(model_path, STAMP)
        print("🚀 Auto-loaded STAMP model + DB mappings at startup!")

    except Exception as e:
        import traceback
        print("❌ STAMP auto-load failed!")
        print(traceback.format_exc())


# Run auto-loader in a background thread (safe even if multiple Django workers)
threading.Thread(target=_auto_load_stamp_model_once, daemon=True).start()