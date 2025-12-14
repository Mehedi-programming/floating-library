from rest_framework import serializers
from .models import *
from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer


# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ["id", "email"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Catregory
        fields = ['id', "name"]


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id", "user", "content", "parent",
            "replies", "created_at", "upvotes", 
            "downvotes"
            ]

    def get_replies(self, obj):
        qs = obj.replies.all()
        return CommentSerializer(qs, many=True).data

import requests
from django.core.files.base import ContentFile

class BookCreateUpdateSerializer(serializers.ModelSerializer):
    category = serializers.CharField(write_only=True, required=False)
    owner = UserSerializer(read_only=True)
    image_url = serializers.URLField(write_only=True, required=False)

    class Meta:
        model = Book
        fields = [
            "id", "title", "author",
            "published_date", "book_image",
            "language", "owner", "category",
            "short_description", "image_url"
        ]

    def create(self, validated_data):
        category = validated_data.pop("category", None)
        image_url = validated_data.pop("image_url", None)
        owner = self.context['request'].user
        book = Book.objects.create(owner=owner, **validated_data)
        file_image = validated_data.get("book_image", None)

        if category:
            category_obj, _ = Catregory.objects.get_or_create(name=category.strip().lower())
            book.category = category_obj
            book.save()
            
        if file_image:
            pass

        if image_url:
            try:
                response = requests.get(image_url)
                if response.status_code == 200:
                    filename = image_url.split("/")[-1]
                    book.book_image.save(filename, ContentFile(response.content), save=True)
                else:
                    raise serializers.ValidationError({"image_url": "Invalid image URL"})
            except Exception as e:
                raise serializers.ValidationError({"image_url": "Can't upload the URL"})

        book.save()
        return book

    def update(self, instance, validated_data):
        category = validated_data.pop('category', None)
        instance.title = validated_data.get('title', instance.title)
        instance.author = validated_data.get('author', instance.author)
        instance.published_date = validated_data.get('published_date', instance.published_date)
        instance.book_image = validated_data.get('book_image', instance.book_image)
        instance.language = validated_data.get('language', instance.language)
        instance.short_description = validated_data.get('short_description', instance.short_description)

        if category:
            category_obj, _ = Catregory.objects.get_or_create(name=category.strip().lower())
            instance.category = category_obj
        instance.save()
        return instance


class BookDetailSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    is_available = serializers.SerializerMethodField()
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'published_date',
            'book_image', 'language', 'created_at', 'updated_at',
            'slug', 'category', 'owner', 'comments', 'short_description', 'is_available',
        ]

    def get_is_available(self, obj):
        return obj.is_available
    
    


class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["id", "title", "author",  "book_image"]


class BorrowRequestSerializer(serializers.ModelSerializer):
    requester = UserSerializer(read_only=True)
    owner = UserSerializer(read_only=True)
    book = BookDetailSerializer(read_only=True)

    class Meta:
        model = BorrowRequest
        fields = ['id', 'requester', 'owner', 'book', 'status', 'created_at']


class WishListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    book = BookListSerializer(read_only=True)

    class Meta:
        model = WishList
        fields = ['id', 'user', 'book', 'added_at']

    