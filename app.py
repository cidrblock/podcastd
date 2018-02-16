import json
import asyncio
from threading import Thread
import functools
import peewee
import settings
from podcastd.log import Logger
from flask import Flask, request
from podcastd import Podcast, Episode, BaseModel, DateTimeEncoder
from podcastd.utils import slack
from playhouse.shortcuts import model_to_dict


def worker(loop):
    """ Create an event loop
    """
    asyncio.set_event_loop(loop)
    loop.run_forever()

app = Flask(__name__)

cls_logger = Logger(settings=settings)
app = cls_logger.add_loggers(flask_app=app)
worker_loop = asyncio.new_event_loop()
worker = Thread(target=worker, args=(worker_loop,))
worker.start()

def update_episodes():
    added = 0
    downloaded = 0
    removed = 0
    for podcast in Podcast.select():
        added += podcast.download_feed()
        removed += podcast.remove_expired_episodes()
        downloaded += podcast.download_new(base_dir=settings.BASE_DIR)
    app.logger.info("Added: %s, Downloaded: %s, Removed: %s" % (added, downloaded, removed))
    if settings.SLACK_URL:
        slack(added=added, removed=removed, downloaded=downloaded, webhook_url=settings.SLACK_URL)

def log(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        app.logger.debug("%s %s" % (request.method, request.url))
        return func(*args, **kwargs)
    return wrapper

@app.route('/episode/<int:episode_id>', methods=['GET'])
@log
def episode(episode_id):
    """ Retrieve an episode by id
    """
    response = [model_to_dict(x)
                for x in Episode.select().where(Episode.id == episode_id)]
    if len(response) == 1:
        return json.dumps(response[0], cls=DateTimeEncoder)
    return json.dumps({"error": "Not found"}), 400

@app.route('/episodes/<int:podcast_id>', methods=['GET'])
@log
def episodes(podcast_id):
    """ Retrieve all episode for a podcast by id
    """
    podc = Podcast.get(Podcast.id == podcast_id)
    response = [model_to_dict(x)
                for x in Episode.select().where(Episode.podcast == podc)]
    return json.dumps(response, cls=DateTimeEncoder)

@app.route('/podcast/<int:podcast_id>', methods=['GET', 'PUT'])
@log
def podcast_get(podcast_id):
    """ Retreive a podcast by id
    """
    if request.method == 'GET':
        response = [model_to_dict(x)
                    for x in Podcast.select().where(Podcast.id == podcast_id)]
        if len(response) == 1:
            return json.dumps(response[0], cls=DateTimeEncoder)
        return json.dumps({"error": "Not found"}), 400
    elif request.method == 'PUT':
        podcast = Podcast.get_or_none(Podcast.id == podcast_id)
        if podcast:
            for key, value in request.get_json().items():
                setattr(podcast, key, value)
            podcast.save()
            return json.dumps(model_to_dict(podcast), cls=DateTimeEncoder)
        return json.dumps({"error": "Not found"}), 400

@app.route('/podcast', methods=['POST'])
@log
def podcast_post():
    """ Create a new podcast subscription
    """
    details = request.get_json()
    podcast = Podcast(**details)
    try:
        podcast.save()
        podcast.build_directory(base_dir=settings.BASE_DIR)
        response = [model_to_dict(x)
                    for x in Podcast.select().where(Podcast.name == details['name'])]
        return json.dumps(response[0], cls=DateTimeEncoder)
    except peewee.IntegrityError as err:
        app.logger.debug(err)
        return json.dumps({"error": "Duplicate"}), 400

@app.route('/podcasts', methods=['GET'])
@log
def podcasts():
    """ Retreive all podcasts
    """
    response = [model_to_dict(x) for x in Podcast.select()]
    return json.dumps(response, cls=DateTimeEncoder)

@app.route('/update', methods=['POST'])
@log
def update():
    """ Trigger an update
    """
    worker_loop.call_soon_threadsafe(update_episodes)
    return json.dumps({"status": "ok"})

if __name__ == '__main__':
    BaseModel().database.create_tables([Podcast, Episode])
    app.logger.info("Starting.")
    app.run(debug=settings.FLASK_DEBUG, host='0.0.0.0', threaded=False)
