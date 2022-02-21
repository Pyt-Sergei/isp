from flask import Blueprint, request, jsonify, g, session
from sqlalchemy.exc import NoResultFound

from flaskr.tasks import download_file, delete_file
from flaskr.utils import get_files_path
from flaskr.auth import login_required

from flaskr.database import Session
from flaskr.models import Archive

import io

bp = Blueprint('main', __name__)


@bp.route('/')
async def home():
    return jsonify(message='Welcome to the web archive download tool')


@bp.route('/user')
@login_required
async def user_page():
    # Users page, displays all files he has been downloaded
    if g.user is not None:
        info = {
            'user': g.user.username,
        }
        for item in Session.query(
                Archive.id, Archive.name, Archive.date, Archive.size).filter(Archive.user_id == g.user.id).all():

            info[item.id] = {}
            info[item.id]['name'] = item.name
            info[item.id]['size'] = item.size
            info[item.id]['date'] = item.date
        return info
    return jsonify(message="You are not logged in")


@bp.route('/archive/', methods=('POST', 'GET'))
@login_required
async def download_archive():
    if request.method == 'POST':
        url = request.form.get('url')
        file = request.files.get('file')

        if url:
            task = download_file.delay(url, user_id=session.get('user_id'))
        elif file:
            in_memory_file = io.BytesIO()
            file.save(in_memory_file)
            task = download_file.apply_async(
                kwargs={'file': in_memory_file, 'user_id': session.get('user_id')}, serializer='pickle')
        else:
            return jsonify(error="Chose a file or provide a url")
        return {'id': task.id}

    return jsonify(
        message="On this page you can download .tar archives using post requests. "
        "Post url:'url' to download and unpack an archive"
    )


@bp.route('/archive/<string:task_id>')
@login_required
async def get_status(task_id):
    task = download_file.AsyncResult(task_id)

    if task.state == 'PENDING':
        return {'error': "The task doesn't exists"}, 404

    if task.failed():
        return {'error': 'The task is failed'}, 404

    elif task.state == 'RETRY':
        return {'error': 'The task is to be retried'}, 404

    elif task.successful():
        try:
            archive_path = Session.query(Archive.archive_path).filter(Archive.id == task.id).one()[0]
            Session.remove()
        except NoResultFound:
            return {'message': 'Archive was deleted'}, 404

        response = {
            'status': 'ok',
            'files': get_files_path(archive_path)
        }
        return response

    response = {'status': task.state}
    if task.result:
        response.update(task.result)    # task.result = {'PROGRESS': X (int)}
    return response


@bp.route('/archive/<string:task_id>', methods=('DELETE',))
@login_required
async def delete(task_id):
    response = delete_file.delay(task_id).get()
    return jsonify(message=response)
