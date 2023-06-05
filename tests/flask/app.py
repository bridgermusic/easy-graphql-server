from flask import Flask
from flask_login import LoginManager

from ..methods.schema1 import schema as methods_schema
from .login import get_user

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.user_loader(get_user)

app.add_url_rule(
    rule="/graphql-methods",
    endpoint="methods_schema",
    view_func=methods_schema.as_flask_view(),
    methods=("GET", "POST"),
)
