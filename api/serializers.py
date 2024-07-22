from rest_framework import serializers
from .models import User, Tweet, Hashtag, Url, UserMention, Symbol

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = '__all__'

class UrlSerializer(serializers.ModelSerializer):
    class Meta:
        model = Url
        fields = '__all__'

class UserMentionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMention
        fields = '__all__'

class SymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symbol
        fields = '__all__'

class TweetSerializer(serializers.ModelSerializer):
    hashtags = HashtagSerializer(many=True, read_only=True)
    urls = UrlSerializer(many=True, read_only=True)
    user_mentions = UserMentionSerializer(many=True, read_only=True)
    symbols = SymbolSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Tweet
        fields = '__all__'
