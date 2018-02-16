"""Logger"""

import errno
import os
import copy
import logging
from logging import getLogger
from logging.handlers import TimedRotatingFileHandler
from . import constants as C

class SimpleFormatter(logging.Formatter):
    """ A simple class to format log output
    """
    def __init__(self, app_name):
        self.app_name = app_name
        self.FORMAT = ('%(asctime)s - %(app_name)s:%(name)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d ')
        msg = self.formatter_msg(self.FORMAT)
        logging.Formatter.__init__(self, msg)

    def format(self, record):
        record.app_name = self.app_name
        return logging.Formatter.format(self, record)

    def formatter_msg(self, msg):
        return msg

class ColorFormatter(logging.Formatter):
    """ A simple class to color log output
    """

    COLORS = {}
    COLORS['WARNING'] = "\033[%sm" % (";".join([C.BOLD, C.FG_YELLOW]))
    COLORS['INFO'] = "\033[%sm" % (";".join([C.NO_EFFECT, C.FG_GREEN]))
    COLORS['DEBUG'] = "\033[%sm" % (";".join([C.NO_EFFECT, C.FG_BLUE]))
    COLORS['CRITICAL'] = "\033[%sm" % (";".join([C.BOLD, C.FG_RED]))
    COLORS['ERROR'] = "\033[%sm" % (";".join([C.NO_EFFECT, C.FG_RED]))
    COLORS['NAME'] = "\033[%sm" % (";".join(C.FAINT))

    def __init__(self, app_name, use_color=True):
        self.FORMAT = ("[$NAME%(app_name)-10s$RESET][$NAME%(name)-30s$RESET][%(levelname)19s] "
                       "%(message)s "
                       "(%(filename)s:%(lineno)d)")
        self.app_name = app_name
        msg = self.formatter_msg(self.FORMAT)
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def formatter_msg(self, msg):
        """ Formats a console message with fancy colors
        """
        msg = msg.replace("$NAME", self.COLORS['NAME'])
        msg = msg.replace("$RESET", C.RESET_SEQ)
        return msg

    def format(self, record):
        colored_record = copy.copy(record)
        colored_record.app_name = self.app_name
        levelname = colored_record.levelname
        levelname_color = self.COLORS[levelname] + levelname + C.RESET_SEQ
        colored_record.levelname = levelname_color
        return logging.Formatter.format(self, colored_record)

def mkdir_p(path):
    """ Make a directory if it deosn't exists

    Args:
        path (string): The directory to ensure

    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
class Logger:
    def __init__(self, settings):
        """ Init the logger

            Args:
                settings (obj): The settings

        """
        self.settings = settings

    def add_loggers(self, flask_app=None):
        """ Add the default, module and app loggers

            Args:
                flask_app (App): A flask app

            Returns:
                App: A flask app
        """
        # Set up the default logger
        logger = logging.getLogger()
        logger.handlers = []
        logger.addHandler(self.console_handler())
        logger.addHandler(self.file_handler())
        logger.setLevel(self.settings.logging_levels['default'])
        # Set up each of the module loggers
        for name, log_level in self.settings.logging_levels.items():
            if name == 'app.logger' and flask_app:
                flask_app = self.flask_app_logger(flask_app=flask_app, log_level=log_level)
            else:
                getLogger(name).handlers = []
                getLogger(name).addHandler(self.console_handler())
                getLogger(name).addHandler(self.file_handler())
                getLogger(name).setLevel(log_level)
                getLogger(name).propagate = False

        # Set the flask app to default if not specified
        if flask_app and 'app.logger' not in self.settings.logging_levels:
            flask_app = self.flask_app_logger(flask_app=flask_app,
                                              log_level=self.settings.logging_levels['default'])

        if flask_app:
            return flask_app
        return None

    def flask_app_logger(self, flask_app, log_level):
        """ Set up the flask app logging

            Args:
                flask_app (App): A flask app
                log_level (str): A log level

            Returns:
                App: The flask app

        """
        flask_app.logger.handlers = []
        flask_app.logger.addHandler(self.console_handler())
        flask_app.logger.addHandler(self.file_handler())
        flask_app.logger.setLevel(log_level)
        flask_app.logger.propagate = False
        return flask_app

    def console_handler(self):
        """ Set up the console logger
        """
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.getLevelName(self.settings.LOGGING_LEVEL_CONSOLE))
        console_handler.setFormatter(ColorFormatter(app_name=self.settings.APP_NAME))
        return console_handler

    def file_handler(self):
        """ Set up a file handler
        """
        mkdir_p(os.path.dirname(self.settings.LOGGING_FILE_PATH))
        file_handler = TimedRotatingFileHandler(self.settings.LOGGING_FILE_PATH,
                                                when=self.settings.LOGGING_ROTATE_WHEN,
                                                interval=self.settings.LOGGING_ROTATE_INTERVAL,
                                                backupCount=self.settings.LOGGING_ROTATE_BACKUP_COUNT)
        file_handler.setLevel(logging.getLevelName(self.settings.LOGGING_LEVEL_FILE))
        file_handler.setFormatter(SimpleFormatter(app_name=self.settings.APP_NAME))
        return file_handler
