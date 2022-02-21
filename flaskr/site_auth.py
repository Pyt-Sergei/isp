import functools

from flask import (
    Blueprint, request, g, url_for, session, flash, redirect, render_template
)
from werkzeug.security import check_password_hash, generate_password_hash

from sqlalchemy.exc import IntegrityError
from flaskr.database import Session
from flaskr.models import User

bp = Blueprint('site_auth', __name__, url_prefix='/site/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                user = User(username, generate_password_hash(password))
                Session.add(user)
                Session.commit()
                Session.remove()
            except IntegrityError:
                error = f"Username {username} is already used."
            else:
                return redirect(url_for('site_auth.login'))

        flash(error, 'error')

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        error = None
        user = Session.query(User).filter(User.username == username).first()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user.password, password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('site_main.user_page', username=username))

        flash(error, 'error')

    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('site_main.home'))


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = Session.query(User).get(user_id)


def login_required(view):
    @functools.wraps(view)
    async def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('site_auth.login'))

        return await view(**kwargs)

    return wrapped_view
