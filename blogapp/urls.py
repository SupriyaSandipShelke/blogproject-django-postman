from django.urls import path
from . import views
from .views import (
    RegisterView,
    LoginView,
    PostListCreateView,
    PostDetailView,
    ForgotPasswordView,
    ResetPasswordView,
    MediaFileListCreateView,
    MediaFileDetailView
)
from blogapp.views import FeedbackView, CacheTestView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # User Authentication
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),

    # JWT Token
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),  # login → get access + refresh
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"), # refresh access token

    # Cache Test
    path('cache-test/', CacheTestView.as_view(), name="cache-test"),

    # Posts
    path("posts/", PostListCreateView.as_view(), name="posts-list-create"),
    path("posts/<int:pk>/", PostDetailView.as_view(), name="post-detail"),

    # Feedback
    path("api/feedback/", FeedbackView.as_view(), name="feedback"),

    # Media Files
    path('media/', MediaFileListCreateView.as_view(), name='media-list-create'),
    path('media/<int:pk>/', MediaFileDetailView.as_view(), name='media-detail'),
]