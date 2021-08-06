## Overview:
  podcastd is a simple podcast downloader written in python. I needed something to run on a pi-zero plugged into the USB port of my i3.

## Features

1) REST API.  The addition of subscriptions and triggering of updates is done using the REST API.
2) Each subscription can have a unique maximum count and maximum age for episodes configured.
3) All ID3 tags are replaced from the downloaded episodes.
4) Images are added to each episodes ID3 tag in the following order of preference:
    * From a URL configured in the DB
    * From the image URL in the episode from the RSS feed
    * From an existing ID3 image
5) Image sizes are set to 400x400px.
6) Post-update summaries can be posted to a slack channel if configured.
7) Episode are renamed to their title in the podcast and stored in directories based on the subscription name.
7) Note: The genre for each episode is set to `255, Podcast`.  This was done so the BMW i-drive system can recognize the episode as podcasts instead of music.


## Installation:

1) Clone this repo
2) Set-up a virtual environment and install the requirements.
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
3) Copy the `settings.sample` file to `settings.py` and update the slack URL if desired

4) Update the `settings.py` file as needed to set the base directory for either development or production.

## Starting the server and adding subscriptions

1) Set an environemnt variable to run in development mode.
```
export ENV=dev
```
2) Start the server
```
python app.py
```
3) Add some subscriptions, some helper scripts to convert OMPL files to yaml can be found in the `init` directory. Update the `podcasts.yml` to suit your tastes.

```
pip install pyyaml
python load_podcasts.py
```
This reads podcasts from the `podcasts.yml` file and POSTs them to the API.

## API endpoints

- GET `/podcasts`: Get all podcasts.

```
curl localhost:5000/podcasts | python -m json.tool
```


- GET `/podcast/id`: Get a podcast using it's id.
```
curl localhost:5000/podcast/1 | python -m json.tool
```

- GET `/episodes/id`: Get all episode for a podcast using the podcast id.

```
curl localhost:5000/episodes/1 | python -m json.tool
```

- GET `/episode/id`: Get a episode using it's id.

```
curl localhost:5000/episode/1285 | python -m json.tool
```

- PUT `/podcast/id`: Update a podcast.

```
curl -X PUT localhost:5000/podcast/1 -H "Content-Type: application/json" -d '{
    "id": 1,
    "name": "A Prairie Home Companion: News from Lake Wobegon",
    "image": null,
    "max_age": "7d",
    "max_episodes": 3,
    "url": "https://feeds.publicradio.org/public_feeds/news-from-lake-wobegon/itunes/rss"
}'
```

- POST `/update`: Trigger a update for subscriptions and removal of expired episodes. The update process will run in the background

```
curl -X POST http://localhost:5000/update
```

## Scheduling

Use cron to schedule hourly updates. Add the following to the crontab.

```
10 * * * * curl -X POST localhost:5000/update
```

## Sync to mp3 player

```
rsync -rvu --modify-window=1  "/home/bthornto/github/podcastd/Podcasts" "/run/media/bthornto/MIBAO-M200"
```