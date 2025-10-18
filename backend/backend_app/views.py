import sys, os
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from rest_framework.decorators import action

from .models import RegisteredUser, User, Book, Rating
from .serializers import (
    RegisteredUserSerializer, LoginSerializer,
    UserSerializer, BookSerializer, RatingSerializer
)
from .utils_auth import generate_tokens_for_registered_user
from rest_framework.permissions import IsAuthenticated
from .permissions import IsRegisteredAdmin


MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../model'))
if MODEL_DIR not in sys.path:
    sys.path.append(MODEL_DIR)

from utils import (
    load_model, load_mappings_from_db, recommend_books,
    record_interaction, handle_new_user, handle_new_book
)
try:
    from stamp_model import STAMP
except ModuleNotFoundError:
    # If it's inside utils.py
    from utils import STAMP
from .permissions import BookPermission

# -------------------------
# AUTH VIEWS
# -------------------------
class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisteredUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        handle_new_user(str(user.id))  # Add ML user
        return Response({"message": "Registered successfully", "user_id": user.id}, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        try:
            ru = RegisteredUser.objects.get(username=username)
        except RegisteredUser.DoesNotExist:
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not check_password(password, ru.password):
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate tokens manually
        tokens = generate_tokens_for_registered_user(ru)

        # Add user details (id, username, email)
        tokens.update({
            "user_id": ru.id,
            "username": ru.username,
            "email": ru.email,
        })

        return Response(tokens, status=status.HTTP_200_OK)


# -------------------------
# CRUD: ML Models
# -------------------------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [BookPermission]
    lookup_field = 'book_isbn'
    def destroy(self, request, *args, **kwargs):
        return Response({"error": "❌ Deletion of books is not allowed."},
                        status=status.HTTP_403_FORBIDDEN)
    @action(detail=False, methods=['post'], url_path='bulk')
    def bulk_fetch(self, request):
        """
        POST /api/books/bulk/
        Body: {"isbns": ["0000913154","0001010565", ...]}
        Returns full book objects.
        """
        isbns = request.data.get('isbns', [])
        if not isbns:
            return Response({"error": "No ISBNs provided."}, status=400)
        
        books = Book.objects.filter(book_isbn__in=isbns)
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    @action(detail=False, methods=['get'], url_path=r'search/(?P<query>[^/.]+)')
    def search_books(self, request, query):
        """
        GET /api/books/search/<query>/
        Example: /api/books/search/harry%20potter%20rowling/
        Returns ISBNs ranked by match relevance.
        """
        tokens = [token.strip().lower() for token in query.split() if token.strip()]
        if not tokens:
            return Response({"error": "Empty search query."}, status=400)
        book_scores = {}

        for book in Book.objects.only('book_isbn', 'book_title', 'book_author'):
            text = f"{book.book_title or ''} {book.book_author or ''}".lower()
            score = sum(token in text for token in tokens)
            if score > 0:
                book_scores[book.book_isbn] = score

        ranked_isbns = sorted(book_scores.keys(), key=lambda x: -book_scores[x])
        top_n = int(request.GET.get('limit', 50))
        ranked_isbns = ranked_isbns[:top_n]

        return Response({
            "query": query,
            "matches": ranked_isbns,
            "total_found": len(ranked_isbns)
        })

class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]


# -------------------------
# MODEL OPERATIONS
# -------------------------
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def api_record_interaction(request):
    user_id = request.data.get('user_id')
    book_isbn = request.data.get('book_isbn')
    rating = request.data.get('rating', None)
    implicit = request.data.get('implicit', False)
    res = record_interaction(user_id, book_isbn, rating, implicit)
    return Response(res)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def api_recommend(request, user_id):
    """Get top-k recommendations"""
    top_k = int(request.GET.get('top_k', 5))
    res = recommend_books(str(user_id), top_k)
    return Response(res)

 
class MeAPIView(APIView):
    """
    Returns the currently authenticated user's profile details.
    Works using JWT Authorization header.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # We identify the user via the token (username lookup)
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return Response({"detail": "Authorization header missing or invalid."},
                            status=status.HTTP_401_UNAUTHORIZED)

        # You already have a RegisteredUser, so we can trust the token’s username/email
        # But since your token is manually generated, we’ll use DB lookup
        user = None
        try:
            # Extract user info from JWT (SimpleJWT handles decoding automatically)
            payload = request.user  # not a full Django user, but we’ll handle fallback
            username = getattr(payload, 'username', None)
            if username:
                user = RegisteredUser.objects.filter(username=username).first()
        except Exception:
            user = None

        # Fallback: manually decode from token if necessary
        if not user:
            from rest_framework_simplejwt.authentication import JWTAuthentication
            try:
                validated_token = JWTAuthentication().get_validated_token(auth_header.split()[1])
                username = validated_token.get('username')
                user = RegisteredUser.objects.filter(username=username).first()
            except Exception:
                return Response({"detail": "Invalid or expired token."},
                                status=status.HTTP_401_UNAUTHORIZED)

        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "date_joined": user.date_joined,
        })