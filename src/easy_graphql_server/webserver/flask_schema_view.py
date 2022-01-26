"""
    Definition of `FlaskSchemaView` class
"""

from flask import request
import flask_login

from ._schema_view import SchemaView


class FlaskSchemaView(SchemaView):

    """
        Flask schema view. Used when calling `Schema.as_flask_view()`.
    """

    def view(self):
        """
            Flask view to compute GraphQL request
        """
        return self.compute_response(
            method = request.method,
            headers = request.headers,
            body = request.get_data(as_text=True),
            query = request.args.to_dict(),
            authenticated_user = flask_login.current_user,
        )
