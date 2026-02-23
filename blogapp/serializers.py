# blogapp/serializers.py
from rest_framework import serializers
from .models import User, Post ,Comment
from .models import MediaFile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User(email=validated_data["email"])
        user.set_password(validated_data["password"])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'image', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']
        
class CommentSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.email")

    class Meta:
        model = Comment
        fields = ["user", "text", "created_at"]
        
class PostFeedbackSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.email")
    likes_count = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True)

    class Meta:
        model = Post
        fields = ["id", "title", "author", "likes_count", "comments"]

    def get_likes_count(self, obj):
        return obj.likes.count()        
    
class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = '__all__'        