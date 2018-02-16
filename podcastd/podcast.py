""" The Podcast class
"""
import os
from datetime import datetime, timedelta
import logging

import feedparser
import pytz
from dateutil import parser
from peewee import TextField, IntegerField
from podcastd.base_model import BaseModel
from podcastd.utils import get_valid_filename
from pytimeparse.timeparse import timeparse

class Podcast(BaseModel):
    """ The Podcast class
    """
    name = TextField(unique=True)
    image = TextField(null=True)
    max_age = TextField()
    max_episodes = IntegerField()
    url = TextField()

    def __init__(self, logger=None, *args, **kwargs):
        super(Podcast, self).__init__(self, *args, **kwargs)
        self.logger = logger or logging.getLogger(__name__)

    def build_directory(self, base_dir):
        """ Build a directory for the podcasts

            Args:
                base_dir: The base directory

        """
        if not os.path.exists(base_dir):
            self.logger.debug("Built: %s" % base_dir)
            os.makedirs(base_dir)
        dir_name = "%s/%s" % (base_dir, get_valid_filename(self.name))
        if not os.path.exists(dir_name):
            self.logger.debug("Built: %s" % dir_name)
            os.makedirs(dir_name)

    def download_feed(self):
        """ Download an RSS feed
        """
        from .episode import Episode

        added = 0
        self.logger.info("Getting: %s" % self.name)
        feed = feedparser.parse(self.url)
        for episode in feed['entries']:
            links = [x for x in episode['links'] if x['type'] == 'audio/mpeg']
            published = parser.parse(episode['published'])
            if published.tzinfo is None or published.tzinfo.utcoffset(published) is None:
                published = pytz.utc.localize(published)
            if links:
                exists = Episode.select().where(Episode.episode_id == episode['id'])
                if not exists:
                    if 'image' in episode and 'href' in episode['image']['href']:
                        image = episode['image']['href']
                    else:
                        image = None
                    entry = Episode(author=episode.get('author', self.name),
                                    episode_id=episode['id'],
                                    file_name=None,
                                    image=image,
                                    link=links[0]['href'],
                                    podcast=self,
                                    published=published,
                                    status=None,
                                    title=episode['title'])
                    entry.save()
                    added += 1
        return added

    def download_new(self, base_dir):
        """ Download new episode for a podcast

            Args:
                base_dir: The base directory

        """
        from .episode import Episode
        downloaded = 0
        max_age = timeparse(self.max_age)
        earliest = datetime.now() - timedelta(seconds=max_age)
        episodes = Episode.select().where(Episode.podcast == self)
        episodes = [x for x in episodes]
        sorted_entries = sorted(episodes, key=lambda k: parser.parse(k.published))
        for episode in sorted_entries[-self.max_episodes:]:
            if not episode.status:
                episode_date = parser.parse(episode.published)
                if episode_date.tzinfo is None or episode_date.tzinfo.utcoffset(episode_date) is None:
                    episode_date = pytz.utc.localize(episode_date)
                if episode_date > pytz.utc.localize(earliest):
                    episode.download(base_dir)
                    downloaded += 1
        return downloaded

    def remove_expired_episodes(self):
        """ Remove expired episodes for a podcast
        """
        from .episode import Episode
        removed = 0
        max_age = timeparse(self.max_age)
        earliest = datetime.now() - timedelta(seconds=max_age)
        episodes = Episode.select().where(Episode.podcast == self)
        sorted_entries = sorted(episodes, key=lambda k: parser.parse(k.published))
        for episode in sorted_entries:
            if episode.status == 'downloaded':
                episode_date = parser.parse(episode.published)
                if episode_date < pytz.utc.localize(earliest):
                    episode.delete()
                    removed += 1
        for episode in sorted_entries[0:-self.max_episodes]:
            if episode.status == 'downloaded':
                episode.delete()
                removed += 1
        return removed
