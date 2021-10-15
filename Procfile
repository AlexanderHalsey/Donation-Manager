web: gunicorn donations.wsgi --log-file - 
worker: celery -A donations worker -B -Q celery -l info