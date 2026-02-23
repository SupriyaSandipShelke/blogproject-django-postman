from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
import jwt, random

from .models import User, Post, MediaFile
from .serializers import (
    UserSerializer, LoginSerializer, PostSerializer,
    PostFeedbackSerializer, MediaFileSerializer
)

# =====================================
# JWT Authentication Helper
# =====================================
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh["user_id"] = user.id
    refresh["email"] = user.email
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }

def generate_otp():
    return str(random.randint(100000, 999999))


# =====================================
# Register API
# =====================================
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            send_mail(
                subject="Registration Successful",
                message=f"Hello {user.email}, Your registration was successful!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            return Response(
                {"message": "User registered successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================
# Login API
# =====================================
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            if not check_password(password, user.password):
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

            tokens = get_tokens_for_user(user)

            send_mail(
                subject="Login Successful",
                message=f"Hello {user.email}, You have logged in successfully!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            return Response(
                {"message": "Login successful", "tokens": tokens},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================
# Forgot Password
# =====================================
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")

        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        otp = generate_otp()
        cache.set(f"reset_otp_{email}", otp, timeout=300)

        send_mail(
            subject="Password Reset OTP",
            message=f"Your OTP is {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({"message": "OTP sent"}, status=status.HTTP_200_OK)


# =====================================
# Reset Password
# =====================================
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        new_password = request.data.get("new_password")

        cached_otp = cache.get(f"reset_otp_{email}")

        if not cached_otp:
            return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

        if otp != cached_otp:
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()

        cache.delete(f"reset_otp_{email}")

        return Response({"message": "Password reset successful"})


# =====================================
# POST LIST + CREATE
# =====================================
class PostListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # ADMIN → all posts
        if user.is_staff or user.is_superuser:
            posts = Post.objects.all().order_by("-created_at")

        # NORMAL USER → own posts
        else:
            posts = Post.objects.filter(author=user).order_by("-created_at")

        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================
# POST DETAIL / UPDATE / DELETE
# =====================================
class PostDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return None

    def get(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_staff or request.user.is_superuser or post.author == request.user:
            serializer = PostSerializer(post)
            return Response(serializer.data)

        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    def put(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        if post.author != request.user:
            return Response({"error": "Only owner can update"}, status=status.HTTP_403_FORBIDDEN)

        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        if post.author != request.user:
            return Response({"error": "Only owner can delete"}, status=status.HTTP_403_FORBIDDEN)

        post.delete()
        return Response({"message": "Post deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


# =====================================
# Feedback View
# =====================================
class FeedbackView(APIView):
    def get(self, request):
        posts = Post.objects.all().order_by("-created_at")
        serializer = PostFeedbackSerializer(posts, many=True)
        return Response(serializer.data)


# =====================================
# Cache Test
# =====================================
class CacheTestView(APIView):
    def get(self, request):
        data = cache.get("my_cached_data")
        if data:
            return Response({"message": "From cache", "data": data})

        data = "Hello Supriya 🚀"
        cache.set("my_cached_data", data, timeout=60)
        return Response({"message": "Created", "data": data})


# =====================================
# Media Upload
# =====================================
class MediaFileListCreateView(generics.ListCreateAPIView):
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)


class MediaFileDetailView(generics.RetrieveAPIView):
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileSerializer
    permission_classes = [IsAuthenticated]