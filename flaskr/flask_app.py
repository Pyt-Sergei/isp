from flask import Flask
import os


def create_app():
    # create and configure the app
    app = Flask('flaskr')
    app.config.update(
        SECRET_KEY='dev',
        broker_url=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379'),
        result_backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379'),
    )
    return app


app = create_app()
