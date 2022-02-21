from flaskr.flask_app import app

# registering blueprints
from flaskr import auth
app.register_blueprint(auth.bp)

from flaskr import main
app.register_blueprint(main.bp)

from flaskr import site_main
app.register_blueprint(site_main.bp)

from flaskr import site_auth
app.register_blueprint(site_auth.bp)
