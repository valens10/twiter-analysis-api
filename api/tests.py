from django.test import TestCase, Client
from django.utils import timezone
import json
import urllib
from django.urls import reverse
from rest_framework import status
from api.models import User, Tweet, Hashtag


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            user_id=1,
            id_str="1",
            name="Test User",
            screen_name="testuser",
            location="Test Location",
            url="http://example.com",
            description="Test description",
            protected=False,
            followers_count=10,
            friends_count=5,
            listed_count=2,
            created_at=timezone.now(),  # Set created_at field
            favourites_count=1,
            utc_offset=None,
            time_zone=None,
            geo_enabled=False,
            verified=False,
            statuses_count=100,
            lang="en",
            contributors_enabled=False,
            is_translator=False,
            is_translation_enabled=False,
            profile_background_color="000000",
            profile_background_image_url="http://example.com/bg.jpg",
            profile_background_image_url_https="https://example.com/bg.jpg",
            profile_background_tile=False,
            profile_image_url="http://example.com/image.jpg",
            profile_image_url_https="https://example.com/image.jpg",
            profile_banner_url="http://example.com/banner.jpg",
            profile_link_color="000000",
            profile_sidebar_border_color="000000",
            profile_sidebar_fill_color="ffffff",
            profile_text_color="000000",
            profile_use_background_image=False,
            default_profile=True,
            default_profile_image=False,
            following=None,
            follow_request_sent=None,
            notifications=None
        )

    def test_user_creation(self):
        self.assertEqual(self.user.screen_name, "testuser")
        self.assertEqual(self.user.followers_count, 10)

class TweetModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            user_id=1,
            id_str="1",
            name="Test User",
            screen_name="testuser",
            created_at=timezone.now()  # Set created_at field
        )
        self.tweet = Tweet.objects.create(
            tweet_id=1,
            id_str="1",
            created_at=timezone.now(),
            text="This is a test tweet",
            source="web",
            truncated=False,
            in_reply_to_status_id=None,
            in_reply_to_status_id_str=None,
            in_reply_to_user_id=None,
            in_reply_to_user_id_str=None,
            in_reply_to_screen_name=None,
            user=self.user,
            geo=None,
            coordinates=None,
            place=None,
            contributors=None,
            retweet_count=0,
            favorite_count=0,
            favorited=False,
            retweeted=False,
            possibly_sensitive=None,
            filter_level=None,
            lang="en",
            retweeted_status=None
        )

    def test_tweet_creation(self):
        self.assertEqual(self.tweet.text, "This is a test tweet")
        self.assertEqual(self.tweet.user.screen_name, "testuser")
        

class UserRecommendationViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Create users
        self.user = User.objects.create(
            user_id=1,
            id_str="1",
            name="Test User",
            screen_name="testuser",
            created_at=timezone.now()
        )

        self.user2 = User.objects.create(
            user_id=2,
            id_str="2",
            name="Test User 2",
            screen_name="testuser2",
            created_at=timezone.now()
        )

        # Create tweets
        self.tweet1 = Tweet.objects.create(
            tweet_id=1,
            id_str="1",
            created_at=timezone.now(),
            text="This is a test tweet with #hashtag1",
            source="web",
            user=self.user2,
            lang="en"
        )

        self.tweet2 = Tweet.objects.create(
            tweet_id=2,
            id_str="2",
            created_at=timezone.now(),
            text="This is another test tweet with #hashtag2",
            source="web",
            user=self.user2,
            lang="en",
            in_reply_to_user_id=1
        )

        self.tweet3 = Tweet.objects.create(
            tweet_id=3,
            id_str="3",
            created_at=timezone.now(),
            text="This is a retweet",
            source="web",
            user=self.user2,
            lang="en",
            retweeted_status=self.tweet1
        )

        # Create hashtags
        self.hashtag1 = Hashtag.objects.create(
            text="hashtag1",
            indices=[0, 8],
            tweet=self.tweet1
        )

        self.hashtag2 = Hashtag.objects.create(
            text="hashtag2",
            indices=[0, 8],
            tweet=self.tweet2
        )

    def test_user_recommendation_view(self):
        # Mock popular hashtags file with excluded hashtags
        popular_hashtags = ["hashtag3", "hashtag4"]  # Excluded hashtags
        file_path = './dataset/popular_hashtags.json'
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(popular_hashtags, f)

        # Prepare the request parameters
        user_id = 1
        tweet_type = "both"
        phrase = urllib.parse.quote("test")
        hashtag = urllib.parse.quote("hashtag1")

        # Make the request
        response = self.client.get(reverse('user-recommendations'), {
            'user_id': user_id,
            'type': tweet_type,
            'phrase': phrase,
            'hashtag': hashtag
        })

        # Check the response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the response data
        response_data = response.json()
        self.assertEqual(len(response_data), 1)  # Adjust based on expected output
        self.assertEqual(response_data[0]['screen_name'], "testuser2")
        self.assertEqual(response_data[0]['contact_tweet_text'], "This is another test tweet with #hashtag2")

    def tearDown(self):
        import os
        file_path = './dataset/popular_hashtags.json'
        if os.path.exists(file_path):
            os.remove(file_path)
