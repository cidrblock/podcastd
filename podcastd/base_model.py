""" The basemodel inherited by all peewee models
"""
import peewee
import logging

# pylint: disable=C0103
db = peewee.SqliteDatabase('podcastd.db')

class BaseModel(peewee.Model): # pylint: disable=R0903
    """ The basemodel inherited by all peewee models
    """
    def __init__(self, *args, **kwargs):
        """ Set the db and init the models
        """
        self.looger = logging.getLogger(__name__)
        self.database = db
        peewee.Model.__init__(self, *args, **kwargs)
    class Meta: # pylint: disable=C1001, W0232, R0903
        """ http://docs.peewee-orm.com/en/latest/peewee/models.html#model-options
        """
        database = db
