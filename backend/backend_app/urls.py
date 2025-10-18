from django.urls import path, include
from rest_framework.routers import DefaultRouter
from backend_app import views

router = DefaultRouter()
router.register(r'ml_users', views.UserViewSet, basename='mluser')
router.register(r'books', views.BookViewSet, basename='book')
router.register(r'ratings', views.RatingViewSet, basename='rating')

urlpatterns = [
    path('api/auth/register/', views.RegisterAPIView.as_view(), name='register'),
    path('api/auth/login/', views.LoginAPIView.as_view(), name='login'),

    path('api/model/record/', views.api_record_interaction, name='record_interaction'),
    path('api/model/recommend/<str:user_id>/', views.api_recommend, name='recommend'),
    path('api/auth/me/', views.MeAPIView.as_view(), name='me'),

    path('api/', include(router.urls)),
]
