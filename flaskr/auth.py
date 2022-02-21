import functools

from flask import (
    Blueprint, request, g, session, jsonify
)
from werkzeug.security import check_password_hash, generate_password_hash

from sqlalchemy.exc import IntegrityError
from flaskr.database import Session
from flaskr.models import User

bp = Blueprint('auth', __name__, url_prefix='/auth')


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
                error = f'Username {username} is already used.'
            else:
                return jsonify(message="You registered successfully!", user=username)

        return jsonify(error=error)

    return jsonify(
        message=f"Welcome to the registration page. "
                f"Register via post-request in format <username:'username', password:'password'>"
    )


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        error = None
        user = Session.query(User).filter(User.username == username).first()

        if user is None:
            error = 'Incorrect username.'
        elif password is None:
            error = 'Incorrect password.'
        elif not check_password_hash(user.password, password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            return jsonify(
                message='You are logged in ! Now you can use all functionality of the service.'
            )
        return jsonify(error=error)

    return jsonify(
        message=f'Welcome to the login page'
    )


@bp.route('/logout')
def logout():
    session.clear()
    return jsonify(message='You logged out')


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
            return jsonify(message='Authorization required')

        return await view(**kwargs)

    return wrapped_view
