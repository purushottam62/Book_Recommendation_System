import os
import sys
import torch
import threading
from collections import defaultdict, deque
from django.db import transaction
import re
from difflib import SequenceMatcher
from django.db.models import Q

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
    try:
    	checkpoint = torch.load(model_path, map_location=_device)
    except Exception as e:
    	print("⚠️ Retrying with weights_only=False due to PyTorch 2.6+ security change...")
    	checkpoint = torch.load(model_path, map_location=_device, weights_only=False)


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

import re
import random
from django.db.models import Q
from backend_app.models import Book

def _get_similar_books_by_title(base_books, limit=500):
    """
    Improved version:
    - Extracts significant keywords (4+ letters, not common stopwords)
    - Matches against title, author, or publisher
    - Ensures results share at least one keyword in the title
    - Adds small randomness for diversity
    """
    if not base_books:
        return list(Book.objects.order_by("?")[:limit])

    # --- Step 1: Build keyword set ---
    stopwords = {
        "from", "with", "this", "that", "your", "have", "will", "book", "books",
        "into", "edition", "press", "about", "their", "these", "those", "which",
        "after", "before", "under", "over", "then", "been", "were", "also",
        "there", "where", "when", "how", "what", "why", "into", "once", "some",
        "more", "most", "other", "such", "many", "each", "than", "them", "they",
        "might", "must", "shall", "could", "would", "very", "make", "made",
        "work", "works", "series", "paperback", "hardcover", "edition", "press"
    }

    keywords = set()
    for book in base_books:
        text = f"{book.book_title or ''} {book.book_author or ''} {book.publisher or ''}".lower()
        tokens = re.findall(r"[a-zA-Z]{4,}", text)
        keywords.update(t for t in tokens if t not in stopwords)

    keywords = list(keywords)[:25]  # limit to avoid giant queries

    if not keywords:
        return list(Book.objects.order_by("?")[:limit])

    # --- Step 2: Query by keyword overlap ---
    query = Q()
    for kw in keywords:
        query |= (
            Q(book_title__icontains=kw)
            | Q(book_author__icontains=kw)
            | Q(publisher__icontains=kw)
        )

    similar_qs = (
        Book.objects.filter(query)
        .distinct()
        .exclude(book_isbn__in=[b.book_isbn for b in base_books])
    )

    # --- Step 3: Rank by title keyword overlap count ---
    matched = []
    for b in similar_qs[:2000]:  # check up to 2000 for efficiency
        title = (b.book_title or "").lower()
        score = sum(kw in title for kw in keywords)
        if score > 0:
            matched.append((score, b))

    # --- Step 4: Sort and add diversity ---
    matched.sort(key=lambda x: x[0], reverse=True)
    books = [b for _, b in matched[: int(limit * 0.8)]]

    # add 20% random books for novelty
    random_books = list(Book.objects.order_by("?")[: int(limit * 0.2)])
    books.extend(random_books)

    # --- Step 5: Deduplicate and trim ---
    seen = set()
    final_books = []
    for b in books:
        if b.book_isbn not in seen:
            seen.add(b.book_isbn)
            final_books.append(b)
        if len(final_books) >= limit:
            break

    print(f"[DEBUG] Found {len(final_books)} similar books (keywords={len(keywords)})")
    return final_books

# --------------------------------------------------------
# INTERACTION FUNCTIONS
# --------------------------------------------------------
def record_interaction(user_id, book_isbn, rating=None, implicit=False):
    """
    Record a user-book interaction.
    - If implicit=True (like a view), assign neutral rating (7.0)
      but only if no explicit rating exists yet.
    - If explicit rating provided, always overwrite any implicit one.
    - Prevent overwriting explicit ratings with implicit ones.
    """
    from backend_app.models import Book, User, Rating

    # --- Resolve user and book ---
    user, _ = User.objects.get_or_create(user_id=user_id)
    book, _ = Book.objects.get_or_create(book_isbn=book_isbn)

    # ✅ Debug print: show full context of incoming request
    print("\n[DEBUG] record_interaction() called:")
    print(f"   → user_id   = {user_id}")
    print(f"   → book_isbn = {book_isbn}")
    print(f"   → book_name = {book.book_title or '(unknown title)'}")
    print(f"   → rating    = {rating}")
    print(f"   → implicit  = {implicit}")
    print("-" * 70)

    # --- Logic for storing rating ---
    existing = Rating.objects.filter(user=user, book=book).first()
    if implicit:
        if existing is None:
            Rating.objects.create(user=user, book=book, rating=7.14)
            msg = f"Implicit (view) rating recorded for {book.book_title or book_isbn}"
        else:
            msg = f"Skipped implicit rating — explicit already exists for {book.book_title or book_isbn}"
    else:
        Rating.objects.update_or_create(
            user=user, book=book,
            defaults={"rating": rating}
        )
        msg = f"Explicit rating {rating} recorded for {book.book_title or book_isbn}"

    # ✅ Debug print: confirm user’s total ratings in DB
    count = Rating.objects.filter(user=user).count()
    print(f"[DEBUG] User {user_id} now has {count} rating(s) in the database.")
    print("=" * 70)

    # --- Update in-memory sequence ---
    _user_sequences[user_id].append(book_isbn)

    return {"status": "ok", "message": msg}


def recommend_books(user_id, top_k=5):
    """
    Hybrid recommend:
    1. Use user's recent rated books (fallback to DB if no session).
    2. Filter candidates by keyword match.
    3. Rank using STAMP.
    4. DO NOT modify user's true session.
    """
    model = _GLOBAL_STATE.get("trained_model")
    if model is None:
        raise ValueError("Model not loaded. Please check auto-load configuration.")

    book_index = _GLOBAL_STATE["book_index"]
    index_book = _GLOBAL_STATE["index_book"]

    # --- Retrieve or reload user session ---
    with _sequence_locks[user_id]:
        seq = list(_user_sequences[user_id])

    if not seq:
        print(f"[DEBUG] No session for {user_id}, loading from DB...")
        from backend_app.models import Rating
        last_rated = (
            Rating.objects.filter(user__user_id=user_id)
            .order_by("-id")
            .values_list("book__book_isbn", flat=True)[:5]
        )
        seq = list(last_rated)
        if seq:
            with _sequence_locks[user_id]:
                _user_sequences[user_id].extend(seq)

    if not seq:
        print(f"[DEBUG] No ratings for user {user_id}, returning fallback.")
        books = list(Book.objects.values_list("book_isbn", flat=True)[:top_k])
        return {"user_id": user_id, "recommendations": books}

    # --- Print last books ---
    last_books = list(Book.objects.filter(book_isbn__in=seq[-5:]))
    print(f"\n[DEBUG] Last {len(last_books)} books for user {user_id}:")
    for b in last_books:
        print(f"   → {b.book_title} ({b.book_isbn})")

    # --- Encode sequence ---
    seq_idx = [book_index[b] for b in seq if b in book_index]
    if not seq_idx:
        return {"user_id": user_id, "recommendations": []}

    seq_tensor = torch.tensor([seq_idx], dtype=torch.long).to(_device)

    # --- Candidates ---
    candidate_books = _get_similar_books_by_title(last_books, limit=100)
    candidate_isbns = [b.book_isbn for b in candidate_books if b.book_isbn in book_index]

    if not candidate_isbns:
        print(f"[DEBUG] No similar books found for user {user_id}.")
        return {"user_id": user_id, "recommendations": []}

    candidate_idxs = [book_index[b] for b in candidate_isbns]
    candidate_tensor = torch.tensor([candidate_idxs], dtype=torch.long).to(_device)

    # --- Score ---
    with torch.no_grad():
        scores = model(seq_tensor, candidate_tensor)
        scores = torch.softmax(scores, dim=-1)
        top_indices = torch.topk(scores, top_k, dim=1).indices.squeeze(0).tolist()

    rec_books = [candidate_isbns[i] for i in top_indices if i < len(candidate_isbns)]

    # --- Print recommendations ---
    rec_objs = list(Book.objects.filter(book_isbn__in=rec_books))
    print(f"\n[DEBUG] Recommended {len(rec_books)} books for user {user_id}:")
    for b in rec_objs:
        print(f"   ★ {b.book_title} ({b.book_isbn})")

    # ✅ DO NOT modify session here!
    print(f"[DEBUG] User {user_id} session remains: {list(_user_sequences[user_id])}")

    return {"user_id": user_id, "recommendations": rec_books}

# -----------------------------------------------
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
            os.path.abspath(os.path.join(os.path.dirname(__file__), "stamp.pt")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../model/stamp.pt")),
            os.path.abspath(os.path.join(os.getcwd(), "model/stamp.pt")),
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
