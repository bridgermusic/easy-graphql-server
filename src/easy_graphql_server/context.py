"""
    Definition of ContextValue class.
"""


class ContextValue:

    # pylint: disable=too-few-public-methods

    """
        `ContextValue` objects are passed as `context_value` parameter to `graphql_sync()`
        method when performing GraphQL queries.
    """

    def __init__(self, authenticated_user):
        self.authenticated_user = authenticated_user
