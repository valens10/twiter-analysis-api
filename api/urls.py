from django.urls import path
from .views import *


urlpatterns = [
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-retrieve-update-destroy'),
    path('tweets/', TweetListCreateView.as_view(), name='tweet-list-create'),
    path('tweets/<int:pk>/', TweetRetrieveUpdateDestroyView.as_view(), name='tweet-retrieve-update-destroy'),
    path('q2/', query_tweets, name='query-tweets'),
    path('user-recommendations/', UserRecommendationView.as_view(), name='user-recommendations'),  # Endpoint for UserRecommendationView
]
