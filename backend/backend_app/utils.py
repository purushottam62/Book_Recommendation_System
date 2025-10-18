from backend_app.models import RegisteredUser, User
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../model')))
from .utils import recommend_books, handle_new_user
from django.db import transaction

@transaction.atomic
def ensure_ml_user_for_registered(username):
    """Ensure that the ML-side User entry exists for a given RegisteredUser."""
    try:
        reg_user = RegisteredUser.objects.get(username=username)
    except RegisteredUser.DoesNotExist:
        return {"error": "User not found"}

    ml_user, created = User.objects.get_or_create(
        user_id=str(reg_user.id),
        defaults={"age": None, "location": ""}
    )

    if created:
        # Also register this user inside ML utils mapping
        handle_new_user(ml_user.user_id)
    return {"status": "ok", "message": f"ML user {'created' if created else 'already exists'}."}


# --------------------------------------------------------------
# Predict Recommendations
# --------------------------------------------------------------
def predict_for_registered_user(username, top_k=5):
    """
    Generate recommendations for a registered Django user
    using the STAMP model utilities from model/utils.py
    """
    try:
        reg_user = RegisteredUser.objects.get(username=username)
    except RegisteredUser.DoesNotExist:
        return {"error": "User not found"}

    # Ensure linked ML user exists
    ensure_ml_user_for_registered(username)
    user_id = str(reg_user.id)

    try:
        return recommend_books(user_id, top_k=top_k)
    except Exception as e:
        return {"error": str(e)}