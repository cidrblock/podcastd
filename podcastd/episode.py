""" The Episode class
"""
import os
import shutil
from datetime import datetime
from io import BytesIO

import requests
import eyed3
from eyed3 import id3
from PIL import Image
import logging
import peewee
from  peewee import TextField, ForeignKeyField, DateTimeField
from podcastd.utils import get_valid_filename
from .base_model import BaseModel
from .podcast import Podcast


class Episode(BaseModel):
    """ The Episode class
    """
    author = TextField()
    downloaded = DateTimeField(null=True)
    episode_id = TextField(unique=True)
    file_name = TextField(null=True)
    image = TextField(null=True)
    link = TextField()
    podcast = ForeignKeyField(Podcast, backref='podcasts')
    published = DateTimeField()
    status = TextField(null=True)
    title = TextField()

    def __init__(self, logger=None, *args, **kwargs):
        """ Init the class, disalbe the invalid tag warnings
        """
        super(Episode, self).__init__(self, *args, **kwargs)
        self.logger = logger or logging.getLogger(__name__)
        self.valid_id3s = [id3.ID3_V1, id3.ID3_V1_0, id3.ID3_V1_1, id3.ID3_V2_3, id3.ID3_V2_4]
        peewee.Model.__init__(self, *args, **kwargs)

    def download(self, base_dir):
        """ Download an episode

            Args:
                base_dir: The base directory in which files should be placed

        """
        fname = "%s/%s/%s" % (base_dir,
                              get_valid_filename(self.podcast.name),
                              get_valid_filename(self.title) + '.mp3')
        self.logger.info("Downloading: %s" % fname)
        response = requests.get(self.link, stream=True)
        with open(fname, 'wb') as fileh:
            shutil.copyfileobj(response.raw, fileh)
        self.file_name = fname
        self.status = 'downloaded'
        self.downloaded = datetime.now()
        self.save()
        self.tag_file()

    def clear_tags(self):
        """ Clear the id3 tags from a file
        """
        current_tag = id3.Tag()
        for entry in self.valid_id3s:
            current_tag.parse(self.file_name, version=entry)
            current_tag.clear()
            current_tag.save(filename=self.file_name, version=entry)

    def tag_file(self):
        """ Add the tags to a file
            Set genre to 255 for compatibility with BMW iDrive

        """
        new_tag = id3.Tag()
        image = self.get_image()
        new_tag.artist = self.author
        new_tag.album_artist = self.author
        new_tag.title = self.title
        new_tag.album = self.podcast.name
        genre = id3.Genre(id=255, name=u"Podcast")
        new_tag.genre = genre
        if image:
            new_tag.images.set(3, image, 'image/jpeg', '')
        self.clear_tags()
        new_tag.save(filename=self.file_name, version=id3.ID3_V2_3)

    def get_image(self):
        """ Get an image for the file
            1) From the image URL in the DB
            2) From the information in the podcast RSS
            3) From the existing id3 tags
        """
        image = None
        if self.podcast.image:
            response = requests.get(self.podcast.image)
            image = Image.open(BytesIO(response.content))
        if not image and self.image:
            response = requests.get(self.image)
            image = Image.open(BytesIO(response.content))
        if not image:
            current_tag = id3.Tag()
            for entry in self.valid_id3s:
                current_tag.parse(self.file_name, version=entry)
                if not image and current_tag.images:
                    image = Image.open(BytesIO(current_tag.images[0].image_data))
                    break
        if image:
            size = 400, 400
            image.thumbnail(size, Image.ANTIALIAS)
            image = image.convert('RGB')
            bytes_io = BytesIO()
            image.save(bytes_io, "JPEG")
            return bytes_io.getvalue()
        return None

    def delete(self):
        """ Delete a file
        """
        if os.path.exists(self.file_name):
            os.remove(self.file_name)
            self.status = 'removed'
            self.save()
            self.logger.debug("Removed: %s" % self.file_name)
