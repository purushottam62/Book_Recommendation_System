from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from backend_app.models import RegisteredUser
from django.conf import settings
import jwt


class RegisteredUserJWTAuthentication(BaseAuthentication):
    """
    Custom JWT authentication for RegisteredUser (non-AbstractUser model).
    """

    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith(f"{self.keyword} "):
            return None

        raw_token = auth_header.split(" ")[1]

        try:
            # Decode manually using Django secret key
            payload = jwt.decode(raw_token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token has expired")
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed("Invalid token")

        user_id = payload.get("user_id") or payload.get("id")
        username = payload.get("username")

        if not user_id and not username:
            raise exceptions.AuthenticationFailed("Token missing user identifiers")

        try:
            # Find RegisteredUser using either ID or username
            user = RegisteredUser.objects.filter(id=user_id).first() or \
                   RegisteredUser.objects.filter(username=username).first()
        except RegisteredUser.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found")

        return (user, None)
