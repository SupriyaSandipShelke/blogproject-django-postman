from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny,IsAuthenticated
from django.contrib.auth.hashers import check_password
from django.conf import settings
from django.http import JsonResponse
from .models import User, Post
from .serializers import UserSerializer, LoginSerializer, PostSerializer
import jwt
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from datetime import datetime, timedelta
from rest_framework import generics
from .models import MediaFile
from .serializers import MediaFileSerializer
from django.core.cache import cache
# =====================================
# JWT Authentication Helper
# =====================================
def authenticate_token(request):
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return None

    try:
        # Expected format: Bearer <token>
        token = auth_header.split(' ')[1]

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )

        user = User.objects.get(id=payload["user_id"])
        return user

    except (jwt.ExpiredSignatureError, jwt.DecodeError, User.DoesNotExist):
        return None

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    # optional custom data inside token
    refresh["user_id"] = user.id
    refresh["email"] = user.email

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
#SIMPLE_JWT = {
#   'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),   # 24 hours
#   'REFRESH_TOKEN_LIFETIME': timedelta(days=100),    # 7 days
#   'AUTH_HEADER_TYPES': ('Bearer',),
#   'ROTATE_REFRESH_TOKENS': True,
#   'BLACKLIST_AFTER_ROTATION': True,
#}

# =====================================
# Register API (Public)
# =====================================
# class RegisterView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = UserSerializer(data=request.data)

#         if serializer.is_valid():
#             serializer.save()
#             return Response(
#                 {"message": "User registered successfully"},
#                 status=status.HTTP_201_CREATED
#             )

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    permission_classes = [AllowAny]
     # 👇 ADD THIS GET METHOD
    def get(self, request):
        return Response(
            {
                "message": "Register API working",
                "usage": "Send POST request with email and password"
            },
            status=status.HTTP_200_OK,
        )
    def post(self, request):
        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
           # tokens = get_tokens_for_user(user)

            return Response(
                {
                    "message": "User registered successfully",
                   # "tokens": tokens,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# =====================================
# Login API (Public)
# =====================================
# class LoginView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = LoginSerializer(data=request.data)

#         if serializer.is_valid():
#             email = serializer.validated_data["email"]
#             password = serializer.validated_data["password"]

#             try:
#                 user = User.objects.get(email=email)

#                 if check_password(password, user.password):
#                     payload = {
#                         "user_id": user.id,
#                         "iat": datetime.utcnow(),
#                         "exp": datetime.utcnow() + timedelta(hours=24)
#                     }

#                     token = jwt.encode(
#                         payload,
#                         settings.SECRET_KEY,
#                         algorithm="HS256"
#                     )

#                     return Response(
#                         {"token": token},
#                         status=status.HTTP_200_OK
#                     )

#                 return Response(
#                     {"error": "Invalid credentials"},
#                     status=status.HTTP_401_UNAUTHORIZED
#                 )

#             except User.DoesNotExist:
#                 return Response(
#                     {"error": "User not found"},
#                     status=status.HTTP_404_NOT_FOUND
#                 )

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]
      # 👇 ADD THIS GET METHOD
    def get(self, request):
        return Response(
            {
                "message": "Login API working",
                "usage": "Send POST request with email and password"
            },
            status=status.HTTP_200_OK,
        )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if not check_password(password, user.password):
                return Response(
                    {"error": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            tokens = get_tokens_for_user(user)

            return Response(
                {
                    "message": "Login successful",
                    "tokens": tokens,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# =====================================
# Create Post (Login Required)
# =====================================
class PostListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cache_key = "post_list"

        # 🔍 Check cache
        cached_data = cache.get(cache_key)

        if cached_data:
            print("🔥 CACHE HIT - Post List")
            return Response(cached_data)

        print("❌ CACHE MISS - Fetching from DB")

        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)

        # 🧠 Store in cache for 2 minutes
        cache.set(cache_key, serializer.data, timeout=120)

        return Response(serializer.data)

    def post(self, request):
        serializer = PostSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(author=request.user)

            # 🔥 Invalidate cache after new post
            cache.delete("post_list")

            print("🗑 Cache Cleared After New Post")

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CacheTestView(APIView):

    def get(self, request):
        data = cache.get("my_cached_data")

        if data:
            print("🔥 Cache HIT")
            return Response({
                "message": "Data from Cache",
                "data": data
            })

        print("❌ Cache MISS")
        data = "Hello Supriya 🚀"

        cache.set("my_cached_data", data, timeout=60)

        return Response({
            "message": "Data created & stored in Cache",
            "data": data
        })
# =====================================
# Retrieve / Update / Delete Post
# =====================================
class PostDetailView(APIView):
    permission_classes = [IsAuthenticated]

    # Helper function to get post by pk and author
    def get_object(self, pk, user):
        try:
            return Post.objects.get(pk=pk, author=user)
        except Post.DoesNotExist:
            return None

    # -------- GET single post --------
    def get(self, request, pk):
        post = self.get_object(pk, request.user)
        if not post:
            return Response(
                {"error": "Post not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PostSerializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # -------- UPDATE post (Author Only) --------
    def put(self, request, pk):
        post = self.get_object(pk, request.user)
        if not post:
            return Response(
                {"error": "Post not found or permission denied"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # -------- DELETE post (Author Only) --------
    def delete(self, request, pk):
        post = self.get_object(pk, request.user)
        if not post:
            return Response(
                {"error": "Post not found or permission denied"},
                status=status.HTTP_404_NOT_FOUND )

        post.delete()
        return Response(
            {"message": "Post deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
class MediaFileListCreateView(generics.ListCreateAPIView):
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] 
    parser_classes = (MultiPartParser, FormParser)

class MediaFileDetailView(generics.RetrieveAPIView):
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileSerializer
    permission_classes = [IsAuthenticated]    
    
        
