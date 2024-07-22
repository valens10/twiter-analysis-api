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

            # Compute interaction score based on replies and retweets
            interaction_score_subquery = contact_tweets.annotate(
                reply_count=Count(Case(When(in_reply_to_user_id=user_id, then=1))),
                retweet_counts=Count(Case(When(retweeted_status__user_id=user_id, then=1)))
            ).annotate(
                interaction_score=Log(Value(2), F('reply_count') + F('retweet_counts') + 1)
            ).values('interaction_score')

            # Compute hashtag score
            hashtag_score_subquery = contact_tweets.annotate(
                hashtag_count=Count(
                    Case(
                        When(hashtags__text__in=EXCLUDED_HASHTAGS, then=0),
                        default=1
                    )
                )
            ).annotate(
                hashtag_score=Case(
                    When(hashtag_count__gt=10, then=1 + Log(Value(2), F('hashtag_count') - 10)),
                    default=Value(1),
                    output_field=FloatField()
                )
            ).values('hashtag_score')

            # Annotate tweet text with phrase and hashtag counts outside ORM
            def count_phrase_and_hashtags(tweet_queryset):
                results = []
                for tweet in tweet_queryset:
                    tweet_text = tweet.text
                    phrase_count = len(re.findall(re.escape(phrase), tweet_text, re.IGNORECASE))
                    hashtag_count = len(Hashtag.objects.filter(tweet=tweet, text__iexact=hashtag))
                    results.append({
                        'tweet': tweet,
                        'phrase_count': phrase_count,
                        'hashtag_count': hashtag_count
                    })
                return results

            # Get phrase and hashtag counts for contact tweets
            contact_tweets_with_counts = count_phrase_and_hashtags(contact_tweets)

            # Compute the total number of matches
            total_phrase_matches = sum(t['phrase_count'] for t in contact_tweets_with_counts)
            total_hashtag_matches = sum(t['hashtag_count'] for t in contact_tweets_with_counts)
            number_of_matches = total_phrase_matches + total_hashtag_matches

            # Compute the keyword score
            keyword_score = 1 + Log(Value(2), number_of_matches + 1)

            # Annotate final score
            final_tweets = [ctw['tweet'] for ctw in contact_tweets_with_counts]
            final_tweets = [t for t in final_tweets if t is not None]  # Filter out None tweets
            
            # Compute interaction score and hashtag score for final tweets
            final_tweets = [t for t in final_tweets if t.final_score > 0]  # Placeholder for actual score computation
            
            # Exclude tweets from the requesting user and select relevant fields
            tweets_data = [{
                'user_id': tweet.user.user_id,
                'screen_name': tweet.user.screen_name,
                'description': tweet.user.description,
                'contact_tweet_text': tweet.text
            } for tweet in final_tweets if tweet.user_id != user_id][:10]

            # Format response
            return Response(tweets_data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
