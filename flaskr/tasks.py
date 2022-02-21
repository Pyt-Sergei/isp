from celery.signals import after_task_publish

from flaskr.celery_app import make_celery
from flaskr.celery_app import celery
from flaskr.utils import get_size, delete, unpack, download, upload
from flaskr.database import Session
from flaskr.models import Archive

import uuid
import os


DOWNLOAD_FOLDER = 'flaskr/downloads/'
UNPACKING_FOLDER = 'flaskr/unpack/'


if not os.path.exists(DOWNLOAD_FOLDER):
    os.mkdir(DOWNLOAD_FOLDER)
if not os.path.exists(UNPACKING_FOLDER):
    os.mkdir(UNPACKING_FOLDER)


@after_task_publish.connect
def update_sent_state(sender=None, headers=None, body=None, **kwargs):
    # indicate whether the task was registered or not
    task = celery.tasks.get(sender)
    backend = task.backend if task else celery.backend

    backend.store_result(body['id'], None, "SENT")


@celery.task(bind=True)
def download_file(self, url=None, file=None, user_id=None):

    filename = f"{uuid.uuid4()}.tar.gz"
    tarfile_path = DOWNLOAD_FOLDER + filename
    archive_path = UNPACKING_FOLDER + filename + '/'

    if url:
        # Writing to file 'tarfile_path' from the url
        download(self, tarfile_path, url)

    elif file:
        # Writing an uploaded file to file 'tarfile_path'
        upload(self, tarfile_path, file)

    # Unpacking an archive_path from tarfile_path into archive_path directory
    unpack(self, tarfile_path, archive_path)

    # Save in database
    obj = Archive(
        id=self.request.id,
        name=filename,
        archive_path=archive_path,
        tarfile_path=tarfile_path,
        size=get_size(tarfile_path),
        user_id=user_id
    )
    Session.add(obj)
    Session.commit()
    Session.remove()


@celery.task()
def delete_file(task_id):
    obj = Session.query(Archive).get(task_id)

    if not obj:
        return "Archive doesn't exists"

    delete(obj.tarfile_path, obj.archive_path)
    Session.delete(obj)
    Session.commit()
    Session.remove()
    return "Archive has been deleted successfully"


