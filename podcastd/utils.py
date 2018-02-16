""" Shared utilities
"""
import re
from datetime import datetime
import json
import requests
from unidecode import unidecode

def get_valid_filename(string):
    """ Return a filename given a string

        Args:
            string (str): A string

        Returns:
            str: A good filename
    """
    string = str(string).strip()
    string = re.sub(r'(?u)[^-\w.\s]', '', string)
    string = re.sub(r'\s{2,}', '-', string)
    string = re.sub(r'[-]{2,}', '', string)
    return unidecode(string)

def slack(added, removed, downloaded, webhook_url):
    """ docstring
    """
    title = "Update complete"
    attachments = []
    fields = []
    fields.append({'value': 'Episodes added: %s' % added})
    fields.append({'value': 'Episodes downloaded: %s' % downloaded})
    fields.append({'value': 'Episodes removed: %s' % removed})
    color = 'good'
    attachments.append({
        'title': title,
        'fields': fields,
        'color': color,
        'mrkdwn_in': ['text', 'fallback', 'fields'],
    })
    payload = {
        'parse': 'none',
        'attachments': attachments
    }
    requests.post(webhook_url, json=payload)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)
