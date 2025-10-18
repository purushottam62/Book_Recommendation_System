from datetime import timedelta
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from backend_app.models import RegisteredUser

def generate_tokens_for_registered_user(user: RegisteredUser):
    """
    Generate JWT access + refresh tokens for a RegisteredUser (non-AbstractUser)
    """
    # Create a dummy RefreshToken manually
    token = RefreshToken()
    # Store identifying info manually (like sub, user_id, username)
    token['user_id'] = str(user.id)
    token['username'] = user.username
    token['email'] = user.email

    # Return tokens as plain strings
    return {
        "refresh": str(token),
        "access": str(token.access_token),
        "user_id": user.id,
        "username": user.username,
        "email": user.email
    }
