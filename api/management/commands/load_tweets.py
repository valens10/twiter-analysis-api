# -- ETL
import os
import sys
sys.path.append('D:/Projects/Coding SLS challenge/twitter_analysis')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'twitter_analysis.settings')
import django
django.setup()
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
import json
from api.models import Hashtag, Symbol, Tweet, Url, User, UserMention
from datetime import datetime

# Define the format for the 'created_at' field
DATE_FORMAT = '%a %b %d %H:%M:%S %z %Y'
ALLOWED_LANGUAGES = {'ar', 'en', 'fr', 'in', 'pt', 'es', 'tr', 'ja'}

class Command(BaseCommand):
    help = 'Load tweets from a JSON file'

    def handle(self, *args, **kwargs):
        print('Starting the command...')
        file_path = './dataset/dataset.json'

        try:
            print(f'Attempting to open file at: {file_path}')
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)  # Attempt to parse JSON data
            print('Data loaded successfully.')
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'File not found: {file_path}'))
            return
        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR('Failed to parse JSON file. The file might be corrupted or improperly formatted.'))
            return
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'An unexpected error occurred: {str(e)}'))
            return

        def process_tweet(tweet_data, parent_tweet=None):
            try:
                print(f'Processing tweet with ID: {tweet_data.get("id_str")}')
                # Extract tweet ID and ID string
                tweet_id = tweet_data.get('id')
                tweet_id_str = tweet_data.get('id_str')
                
                # Extract user data
                user_data = tweet_data.get('user', {})
                user_id = user_data.get('id')
                user_id_str = user_data.get('id_str')
                
                # Check if tweet already exists
                if Tweet.objects.filter(tweet_id=tweet_id).exists():
                    print(f'Tweet with ID {tweet_id} already exists. Skipping creation.')
                    return None
                
                # Check if the tweet language is allowed
                lang = tweet_data.get('lang')
                if lang not in ALLOWED_LANGUAGES:
                    self.stderr.write(self.style.WARNING(f'Tweet language "{lang}" not allowed. Skipping tweet.'))
                    return None
                
                # Check if both tweet ID and ID string are missing or null
                if not tweet_id and not tweet_id_str:
                    self.stderr.write(self.style.WARNING(f'Malformed tweet (missing both id and id_str): {tweet_data}'))
                    return None

                # Check if both user ID and ID string are missing or null
                if not user_id and not user_id_str:
                    self.stderr.write(self.style.WARNING(f'Malformed user (missing both id and id_str): {tweet_data}'))
                    return None

                # Check if created_at is missing or null
                created_at_str = tweet_data.get('created_at')
                if not created_at_str:
                    self.stderr.write(self.style.WARNING(f'Malformed tweet (missing created_at): {tweet_data}'))
                    return None
                
                # Parse the created_at field
                created_at = datetime.strptime(created_at_str, DATE_FORMAT)
                if created_at is None:
                    self.stderr.write(self.style.WARNING(f'Malformed tweet (invalid created_at format): {tweet_data}'))
                    return None

                # Check if text is missing or null or empty
                text = tweet_data.get('text', '')
                if not text:
                    self.stderr.write(self.style.WARNING(f'Malformed tweet (missing or empty text): {tweet_data}'))
                    return None

                # Extract and validate hashtag array
                hashtags = tweet_data.get('entities', {}).get('hashtags', [])
                if hashtags is None or (isinstance(hashtags, list) and len(hashtags) == 0):
                    self.stderr.write(self.style.WARNING(f'Malformed tweet (hashtags array missing or empty): {tweet_data}'))
                    return None

                # Create or update the User object
                user_created_at =  user_data.get('created_at', None)
                if user_created_at:
                    user_created_at = datetime.strptime(user_data.get('created_at'), DATE_FORMAT)
                    
                user, created = User.objects.get_or_create(
                    user_id=user_id,
                    defaults={
                        'id_str': user_id_str,
                        'name': user_data.get('name'),
                        'screen_name': user_data.get('screen_name'),
                        'location': user_data.get('location', ''),
                        'url': user_data.get('url'),
                        'description': user_data.get('description'),
                        'protected': user_data.get('protected', False),
                        'followers_count': user_data.get('followers_count', 0),
                        'friends_count': user_data.get('friends_count', 0),
                        'listed_count': user_data.get('listed_count', 0),
                        'created_at': user_created_at,
                        'favourites_count': user_data.get('favourites_count', 0),
                        'utc_offset': user_data.get('utc_offset'),
                        'time_zone': user_data.get('time_zone'),
                        'geo_enabled': user_data.get('geo_enabled', False),
                        'verified': user_data.get('verified', False),
                        'statuses_count': user_data.get('statuses_count', 0),
                        'lang': user_data.get('lang', ''),
                        'contributors_enabled': user_data.get('contributors_enabled', False),
                        'is_translator': user_data.get('is_translator', False),
                        'is_translation_enabled': user_data.get('is_translation_enabled', False),
                        'profile_background_color': user_data.get('profile_background_color'),
                        'profile_background_image_url': user_data.get('profile_background_image_url'),
                        'profile_background_image_url_https': user_data.get('profile_background_image_url_https'),
                        'profile_background_tile': user_data.get('profile_background_tile', False),
                        'profile_image_url': user_data.get('profile_image_url'),
                        'profile_image_url_https': user_data.get('profile_image_url_https'),
                        'profile_link_color': user_data.get('profile_link_color'),
                        'profile_sidebar_border_color': user_data.get('profile_sidebar_border_color'),
                        'profile_sidebar_fill_color': user_data.get('profile_sidebar_fill_color'),
                        'profile_text_color': user_data.get('profile_text_color'),
                        'profile_use_background_image': user_data.get('profile_use_background_image', False),
                        'default_profile': user_data.get('default_profile', False),
                        'default_profile_image': user_data.get('default_profile_image', False),
                        'following': user_data.get('following'),
                        'follow_request_sent': user_data.get('follow_request_sent'),
                        'notifications': user_data.get('notifications'),
                    }
                )
                # Create the Tweet object
                tweet = Tweet.objects.create(
                    tweet_id=tweet_id,
                    id_str=tweet_id_str,
                    created_at=created_at,
                    text=text,
                    source=tweet_data.get('source'),
                    truncated=tweet_data.get('truncated', False),
                    in_reply_to_status_id=tweet_data.get('in_reply_to_status_id'),
                    in_reply_to_status_id_str=tweet_data.get('in_reply_to_status_id_str'),
                    in_reply_to_user_id=tweet_data.get('in_reply_to_user_id'),
                    in_reply_to_user_id_str=tweet_data.get('in_reply_to_user_id_str'),
                    in_reply_to_screen_name=tweet_data.get('in_reply_to_screen_name'),
                    user=user,
                    geo=tweet_data.get('geo'),
                    coordinates=tweet_data.get('coordinates'),
                    place=tweet_data.get('place'),
                    contributors=tweet_data.get('contributors'),
                    retweet_count=tweet_data.get('retweet_count', 0),
                    favorite_count=tweet_data.get('favorite_count', 0),
                    favorited=tweet_data.get('favorited', False),
                    retweeted=tweet_data.get('retweeted', False),
                    possibly_sensitive=tweet_data.get('possibly_sensitive', False),
                    filter_level=tweet_data.get('filter_level'),
                    lang=tweet_data.get('lang'),
                    retweeted_status=parent_tweet  # Associate with the parent retweet
                )
                
                # Create Hashtag objects
                for hashtag_data in tweet_data.get('entities', {}).get('hashtags', []):
                    Hashtag.objects.get_or_create(
                        text=hashtag_data.get('text'),
                        indices=hashtag_data.get('indices'),
                        tweet=tweet
                    )
                
                # Create Url objects
                for url_data in tweet_data.get('entities', {}).get('urls', []):
                    Url.objects.get_or_create(
                        url=url_data.get('url'),
                        expanded_url=url_data.get('expanded_url'),
                        display_url=url_data.get('display_url'),
                        indices=url_data.get('indices'),
                        tweet=tweet
                    )
                
                # Create UserMention objects
                for mention_data in tweet_data.get('entities', {}).get('user_mentions', []):
                    if not UserMention.objects.filter(id=mention_data.get('id')).exists():
                        UserMention.objects.create(
                            id=mention_data.get('id'),
                            screen_name=mention_data.get('screen_name', ''),
                            name=mention_data.get('name', ''),
                            id_str=mention_data.get('id_str'),
                            indices=mention_data.get('indices'),
                            tweet=tweet
                        )
                
                # Create Symbol objects
                for symbol_data in tweet_data.get('entities', {}).get('symbols', []):
                    Symbol.objects.get_or_create(
                        text=symbol_data.get('text'),
                        indices=symbol_data.get('indices'),
                        tweet=tweet
                    )
                
                return tweet

            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Error processing tweet: {str(e)}'))
                return None

        # Iterate over each tweet item in the JSON data
        print('Processing tweets...')
        for item in data:
            tweet = process_tweet(item)
            
            # Process retweeted statuses in the chain
            retweeted_status_data = item.get('retweeted_status')
            if retweeted_status_data is not None:
                while retweeted_status_data:
                    tweet = process_tweet(retweeted_status_data, parent_tweet=tweet)
                    retweeted_status_data = retweeted_status_data.get('retweeted_status')

        print('Finished processing tweets.')
