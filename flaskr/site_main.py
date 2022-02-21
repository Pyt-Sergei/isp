from flask import Blueprint, request, g, session, render_template, flash, redirect, abort, url_for
from sqlalchemy.exc import NoResultFound

from flaskr.tasks import download_file, delete_file
from flaskr.utils import get_files_path
from flaskr.site_auth import login_required

from flaskr.database import Session
from flaskr.models import Archive, User

import io


bp = Blueprint('site_main', __name__, url_prefix='/site')


@bp.route('/home/')
async def home():
    return render_template('main/home.html')


@bp.route('/user/<string:username>')
@login_required
async def user_page(username=None):
    """ Users page, displays all files he has been downloaded """
    if g.user.username != username:
        abort(404)
    return render_template('main/user_page.html')


@bp.route('user/<string:username>/files/')
@login_required
async def user_files(username):
    user_id = session['user_id']
    archives = Session.query(Archive).filter(Archive.user_id == user_id).all()
    return render_template('main/user_files.html', archives=archives)


@bp.route('/archive/download/', methods=('POST', 'GET'))
@login_required
async def download_archive():
    if request.method == 'POST':
        url = request.form.get('url')
        file = request.files.get('file')

        if url is not None and url != '':
            task = download_file.delay(url, user_id=session.get('user_id'))

            flash(f'Archive id: {task.id}')

        elif file is not None and file.filename != '':
            in_memory_file = io.BytesIO()
            file.save(in_memory_file)
            task = download_file.apply_async(
                kwargs={'file': in_memory_file, 'user_id': session.get('user_id')}, serializer='pickle')

            flash(f'Archive id: {task.id}')

        else:
            flash("Choose a file or provide url", 'error')

    return render_template('main/download.html')


@bp.route('/archive/status/', methods=('POST', 'GET'))
@login_required
async def get_status():
    if request.method == 'POST':
        task_id = request.form.get('task_id')
        return redirect(url_for('.get_file_status', archive_id=task_id))

    return render_template('main/track.html')


@bp.route('/archive/status/<string:archive_id>', methods=('POST', 'GET'))
@login_required
async def get_file_status(archive_id):
    if request.method == 'POST':
        task_id = request.form.get('task_id')
        return redirect(url_for('.get_file_status', archive_id=task_id))

    task_id = archive_id
    task = download_file.AsyncResult(task_id)

    response = {'task_id': task_id}

    if task.state == 'PENDING':
        flash("Archive id doesn't exists", 'error')
        return render_template('main/track.html', response=response)

    if task.failed():
        flash("The task is failed", 'error')
        return render_template('main/track.html', response=response)

    elif task.state == 'RETRY':
        flash("The task is to be retried", 'error')
        return render_template('main/track.html', response=response)

    elif task.successful():
        try:
            archive_path = Session.query(Archive.archive_path).filter(Archive.id == task.id).one()[0]
            Session.remove()
        except NoResultFound:
            flash("Archive was deleted", 'error')
            return render_template('main/track.html', response=response)

        response.update({
            'status': 'ok',
            'files': get_files_path(archive_path)
        })
        return render_template('main/track.html', response=response)

    response.update({'status': task.state})
    if task.result is not None:
        response.update(task.result)  # task.result = {'progress': X (int)}
    return render_template('main/track.html', response=response)


@bp.route('/archive/delete/', methods=('POST', 'GET'))
@login_required
async def delete():
    if request.method == 'POST':
        task_id = request.form.get('task_id')
        return redirect(url_for('.delete_get', archive_id=task_id))
    return render_template('main/delete.html')


@bp.route('/archive/delete/<string:archive_id>', methods=('POST', 'GET'))
@login_required
async def delete_get(archive_id):
    if request.method == 'POST':
        task_id = request.form.get('task_id')
        return redirect(url_for('.delete_get', archive_id=task_id))
    response = delete_file.delay(archive_id).get()
    flash(response)
    return render_template('main/delete.html')

