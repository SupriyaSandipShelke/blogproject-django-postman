from rest_framework import serializers

def validate_file_size(value):
    max_size = 5 * 1024 * 1024  # 5MB

    if value.size > max_size:
        raise serializers.ValidationError("File size must be less than 5MB.")
