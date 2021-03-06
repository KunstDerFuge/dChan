from celery import shared_task
from django.core.cache import cache
import requests

from chanscan.models import Blacklist


@shared_task
def fetch_chanscan_definitions():
    chanscan_api_url = 'https://api.chanscan.com/all'
    response = requests.get(chanscan_api_url)
    blacklist = [blacklist.word for blacklist in Blacklist.objects.all()]
    try:
        data = list(response.json())
        data = [word for word in data if word['definition'] != '' and word['word'] not in blacklist]
        if len(data) > 350:  # Simple sanity check so that we don't overwrite/delete valid definitions in case of errors
            cache.set('definitions', data, None)

    finally:
        # If any exceptions were thrown above, just leave existing definitions as is
        pass
