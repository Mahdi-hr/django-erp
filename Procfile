web: gunicorn erp_project.wsgi
worker: celery -A erp_project worker --loglevel=info
beat: celery -A erp_project beat --loglevel=info
