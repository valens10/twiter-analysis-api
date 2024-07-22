from rest_framework import viewsets
from .models import User, Tweet,Hashtag
from .serializers import UserSerializer, TweetSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Count
from rest_framework.views import APIView
import urllib.parse
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.db.models import Value, F, IntegerField, FloatField, Q, Count, Case, When, OuterRef, Subquery, Sum
from django.db.models.functions import Log
from rest_framework import generics, mixins
import re
from urllib.parse import unquote
import json

# List of hashtags to exclude from the hashtag score calculation
popular_hashtags = './datasets/popular_hashtags.json'
EXCLUDED_HASHTAGS = ['zipcode', 'rwanda']
TEAM_ID = "<YOUR_TEAM_ID>"
TEAM_AWS_ACCOUNT_ID = "<YOUR_AWS_ACCOUNT_ID>"


class UserPagination(PageNumberPagination):
    page_size = 100  # Adjust page size as needed

class UserListCreateView(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    pagination_class = UserPagination
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

class UserRetrieveUpdateDestroyView(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
    
class TweetListCreateView(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    serializer_class = TweetSerializer
    queryset = Tweet.objects.all()
    pagination_class = UserPagination

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

class TweetRetrieveUpdateDestroyView(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = TweetSerializer
    queryset = Tweet.objects.all()

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


@api_view(['GET'])
def query_tweets(request):
    user_id = request.GET.get('user_id')
    query_type = request.GET.get('type')
    phrase = request.GET.get('phrase')
    hashtag = request.GET.get('hashtag')

    # Validate required parameters
    if not all([user_id, query_type, phrase, hashtag]):
        return Response({'error': 'Missing required parameters: user_id, type, phrase, and hashtag are all required.'}, status=status.HTTP_400_BAD_REQUEST)

    if query_type not in ['reply', 'retweet', 'both']:
        return Response({'error': 'Invalid query type. Must be "reply", "retweet", or "both".'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Decode the percent-encoded phrase
        phrase = unquote(phrase)

        # Prepare the filters
        hashtag_filter = Q(hashtags__text__iexact=hashtag)
        text_filter = Q(text__icontains=phrase)

        # Initialize the base query
        base_query = Q()

        if query_type == 'reply':
            base_query &= Q(in_reply_to_user_id=user_id)
            
        elif query_type == 'retweet':
            base_query &= Q(retweeted_status__user__user_id=user_id)

        elif query_type == 'both':
            base_query &= Q(Q(user__user_id=user_id) | Q(in_reply_to_user_id=user_id) | Q(retweeted_status__user__user_id=user_id))

        # Query tweets with the specified filters
        print(base_query & text_filter & hashtag_filter)
        tweets = Tweet.objects.filter(base_query & text_filter & hashtag_filter).order_by('-created_at')

        # Dictionary to hold the latest tweet and user details
        user_details = {}

        for tweet in tweets:
            contact_user_id = tweet.user.user_id
            if contact_user_id not in user_details:
                user_details[contact_user_id] = {
                    'screen_name': tweet.user.screen_name,
                    'description': tweet.user.description,
                    'latest_tweet': tweet.text
                }
            else:
                # Update latest tweet if needed
                user_details[contact_user_id]['latest_tweet'] = tweet.text

        # Prepare response data
        results = []
        for user_id, details in user_details.items():
            results.append({
                'user_id': user_id,
                'screen_name': details['screen_name'],
                'description': details['description'],
                'latest_tweet': details['latest_tweet']
            })

        response_data = {
            'team_id': TEAM_ID,
            'aws_account_id': TEAM_AWS_ACCOUNT_ID,
            'results': results
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'An error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserRecommendationView(APIView):
    def get(self, request):
        file_path = './dataset/popular_hashtags.json'
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                EXCLUDED_HASHTAGS = json.load(f)
        except Exception as e:
            return Response({'detail': 'An unexpected error occurred: ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Retrieve query parameters
            user_id = request.query_params.get('user_id')
            tweet_type = request.query_params.get('type', 'both')
            phrase = urllib.parse.unquote(request.query_params.get('phrase', ''))
            hashtag = urllib.parse.unquote(request.query_params.get('hashtag', ''))

            if not user_id:
                return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Filter tweets by language
            tweets = Tweet.objects.filter(
                lang__in=['ar', 'en', 'fr', 'id', 'pt', 'es', 'tr', 'ja']
            )

            # Filter contact tweets based on the specified type
            if tweet_type == 'reply':
                contact_tweets = tweets.filter(in_reply_to_user_id=user_id)
            elif tweet_type == 'retweet':
                contact_tweets = tweets.filter(retweeted_status__user_id=user_id)
            else:  # both
                contact_tweets = tweets.filter(
                    Q(in_reply_to_user_id=user_id) | Q(retweeted_status__user_id=user_id)
                )

            # Compute scores for each tweet
            def compute_scores(tweet_queryset):
                results = []
                for tweet in tweet_queryset:
                    # Calculate interaction score
                    reply_count = tweet.in_reply_to_user_id == user_id
                    retweet_count = tweet.retweeted_status is not None and tweet.retweeted_status.user_id == user_id
                    interaction_score = 1 + Log(Value(2), (reply_count + retweet_count) + 1)
                    
                    # Calculate hashtag score
                    hashtags = Hashtag.objects.filter(tweet=tweet)
                    hashtag_count = sum(1 for h in hashtags if h.text not in EXCLUDED_HASHTAGS)
                    hashtag_score = Case(
                        When(hashtag_count__gt=10, then=1 + Log(Value(2), hashtag_count - 10)),
                        default=Value(1),
                        output_field=FloatField()
                    )
                    
                    # Calculate phrase count
                    tweet_text = tweet.text
                    phrase_count = len(re.findall(re.escape(phrase), tweet_text, re.IGNORECASE))
                    
                    # Compute final score
                    keyword_score = 1 + Log(Value(2), phrase_count + hashtag_count + 1)
                    
                    results.append({
                        'tweet': tweet,
                        'interaction_score': interaction_score,
                        'hashtag_score': hashtag_score,
                        'keyword_score': keyword_score
                    })
                return results

            # Get scores for contact tweets
            contact_tweets_with_scores = compute_scores(contact_tweets)

            # Rank tweets based on computed scores
            ranked_tweets = sorted(contact_tweets_with_scores, key=lambda x: (
                x['interaction_score'] + x['hashtag_score'] + x['keyword_score']
            ), reverse=True)

            # Select top tweets, excluding the requesting user
            tweets_data = [{
                'user_id': tweet_data['tweet'].user.user_id,
                'screen_name': tweet_data['tweet'].user.screen_name,
                'description': tweet_data['tweet'].user.description,
                'contact_tweet_text': tweet_data['tweet'].text
            } for tweet_data in ranked_tweets if tweet_data['tweet'].user_id != user_id][:10]

            # Format response
            return Response(tweets_data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
