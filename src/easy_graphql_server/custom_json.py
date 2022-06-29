"""
    Module for custom JSON serialization.
"""

import json
import datetime


class JSONEncoder(json.JSONEncoder):

    """
        Overrides `json.JSONEncoder`, with the benefit of being able to serialize
        date, time and datetime instances.
    """

    def default(self, o):
        """
            Overrides `json.JSONEncoder.default`, with the benefit of being able to serialize
            date, time and datetime instances.
        """
        if isinstance(o, (datetime.datetime, datetime.date, datetime.time)):
            return o.isoformat()
        return super().default(o)


dumps = JSONEncoder().encode
