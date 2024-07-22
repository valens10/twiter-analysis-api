from django.db import models
from django.db.models import JSONField # Make sure to use the appropriate JSONField for your Django version

class User(models.Model):
    user_id = models.BigIntegerField(unique=True, primary_key=True)
    id_str = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    screen_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    protected = models.BooleanField(default=False)
    followers_count = models.IntegerField(default=0)
    friends_count = models.IntegerField(default=0)
    listed_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(null=True, blank=True)
    favourites_count = models.IntegerField(default=0)
    utc_offset = models.IntegerField(blank=True, null=True)
    time_zone = models.CharField(max_length=50, blank=True, null=True)
    geo_enabled = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    statuses_count = models.IntegerField(default=0)
    lang = models.CharField(max_length=10, blank=True, null=True)
    contributors_enabled = models.BooleanField(default=False)
    is_translator = models.BooleanField(default=False)
    is_translation_enabled = models.BooleanField(default=False)
    profile_background_color = models.CharField(max_length=6, blank=True, null=True)
    profile_background_image_url = models.URLField(max_length=500, blank=True, null=True)
    profile_background_image_url_https = models.URLField(max_length=500, blank=True, null=True)
    profile_background_tile = models.BooleanField(default=False)
    profile_image_url = models.URLField(max_length=500, blank=True, null=True)
    profile_image_url_https = models.URLField(max_length=500, blank=True, null=True)
    profile_banner_url = models.URLField(max_length=500, blank=True, null=True)
    profile_link_color = models.CharField(max_length=6, blank=True, null=True)
    profile_sidebar_border_color = models.CharField(max_length=6, blank=True, null=True)
    profile_sidebar_fill_color = models.CharField(max_length=6, blank=True, null=True)
    profile_text_color = models.CharField(max_length=6, blank=True, null=True)
    profile_use_background_image = models.BooleanField(default=False)
    default_profile = models.BooleanField(default=False)
    default_profile_image = models.BooleanField(default=False)
    following = models.BooleanField(blank=True, null=True)
    follow_request_sent = models.BooleanField(blank=True, null=True)
    notifications = models.BooleanField(blank=True, null=True)
    
    class Meta:
        db_table = 'tb_tweet_users'
        default_permissions = ()

    def __str__(self):
        return self.screen_name

class Tweet(models.Model):
    tweet_id = models.BigIntegerField(unique=True)
    id_str = models.CharField(max_length=20)
    created_at = models.DateTimeField()
    text = models.TextField()
    source = models.CharField(max_length=255)
    truncated = models.BooleanField(default=False)
    in_reply_to_status_id = models.BigIntegerField(blank=True, null=True)
    in_reply_to_status_id_str = models.CharField(max_length=20, blank=True, null=True)
    in_reply_to_user_id = models.BigIntegerField(blank=True, null=True)
    in_reply_to_user_id_str = models.CharField(max_length=20, blank=True, null=True)
    in_reply_to_screen_name = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    geo = JSONField(blank=True, null=True)
    coordinates = JSONField(blank=True, null=True)
    place = models.TextField(blank=True, null=True)
    contributors = JSONField(blank=True, null=True)
    retweet_count = models.IntegerField(default=0)
    favorite_count = models.IntegerField(default=0)
    favorited = models.BooleanField(default=False)
    retweeted = models.BooleanField(default=False)
    possibly_sensitive = models.BooleanField(blank=True, null=True)
    filter_level = models.CharField(max_length=50, blank=True, null=True)
    lang = models.CharField(max_length=10)
    retweeted_status = models.ForeignKey('self', related_name='retweets', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'tb_tweets'
        default_permissions = ()

    def __str__(self):
        return self.text

class Hashtag(models.Model):
    text = models.CharField(max_length=255)
    indices = JSONField()
    tweet = models.ForeignKey(Tweet, related_name='hashtags', on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'tb_tweet_hashtags'
        default_permissions = ()

    def __str__(self):
        return self.text

class Url(models.Model):
    url = models.URLField(max_length=500)
    expanded_url = models.URLField(max_length=500)
    display_url = models.CharField(max_length=255)
    indices = JSONField()
    tweet = models.ForeignKey(Tweet, related_name='urls', on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'tb_tweet_url'
        default_permissions = ()

    def __str__(self):
        return self.url

class UserMention(models.Model):
    id = models.BigIntegerField(primary_key=True, unique=True)
    screen_name = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    id_str = models.CharField(max_length=20)
    indices = JSONField()
    tweet = models.ForeignKey(Tweet, related_name='user_mentions', on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'tb_tweet_user_mentions'
        default_permissions = ()

    def __str__(self):
        return self.screen_name

class Symbol(models.Model):
    text = models.CharField(max_length=255)
    indices = JSONField()
    tweet = models.ForeignKey(Tweet, related_name='symbols', on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'tb_tweet_symbols'
        default_permissions = ()

    def __str__(self):
        return self.text
