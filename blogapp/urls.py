from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    #PostCreateView,
    #PostListView,
    PostListCreateView,
    PostDetailView
)

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),        # login → get access + refresh
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),       # refresh access token


    #path("posts/", PostListView.as_view()),
     path("posts/", PostListCreateView.as_view()),
   #path("posts/create/", PostCreateView.as_view()),
    path("posts/<int:pk>/", PostDetailView.as_view()),
    
    # ============================
    # Dashboard / Template URLs
    # ============================
]
