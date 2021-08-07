# dChan
Django-powered archive of Q-related chan posts

## Installation

First, create a virtualenv and install requirements:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Now start serving Django locally:
```
python manage.py runserver
```

Next, load the data:
```
python manage.py load_chan_data
```

Process replies (for reply links), 4chan links (for >>links on 4chan threads), search vectors (for efficient full-text search capabilities), and mark Q drops. Each step will take quite a while for large datasets:
```
python manage.py process_replies
python manage.py process_4chan_links
python manage.py process_search_vectors
python manage.py mark_q_drops
```

## Setting up automatic scraping

For dChan's automatic scrape functions, we also need to configue supervisor (to daemonize celery) and scrapyd.

Install supervisord for your server's distribution, example for Ubuntu:
```
sudo apt-get install supervisor
```


Copy the included celery configuration files into supervisor's conf.d directory:
```
sudo cp supervisor/*.conf /etc/supervisor/conf.d
```


Scan and update the conf files with supervisorctl:

```
sudo supervisorctl reread
sudo supervisorctl update
```


Now download Firefox's `geckodriver` to enable archive.is scraping. Download the latest geckodriver release from https://github.com/mozilla/geckodriver/releases, then extract the geckodriver file. Make it executable and move it to /usr/local/bin:
```
chmod +x geckodriver
sudo mv geckodriver /usr/local/bin/
```
