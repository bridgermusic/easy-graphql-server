"""
    This module defines the `LOOKUPS` constant, useful for defining filters on fields.

    This is currently used for Django lookups, but could be very interesting for other ORMs too.
"""


from .. import types


LOOKUPS = {

    types.Boolean: {},

    types.Int: {},

    types.Float: {},

    types.Decimal: {},

    types.String: {
        'iexact': types.String,
        'contains': types.String,
        'icontains': types.String,
        'startswith': types.String,
        'istartswith': types.String,
        'endswith': types.String,
        'iendswith': types.String,
        'regex': types.String,
        'iregex': types.String,
    },

    types.DateTime: {
        'date': types.Date,
        'time': types.Time,
    },

    types.Date: {
        'year': types.Int,
        'iso_year': types.Int,
        'quarter': types.Int,
        'month': types.Int,
        'week': types.Int,
        'iso_week_day': types.Int,
        'week_day': types.Int,
        'day': types.Int,
    },

    types.Time: {
        'hour': types.Int,
        'minute': types.Int,
        'second': types.Int,
    },

}


LOOKUPS[types.DateTime].update(LOOKUPS[types.Date])
LOOKUPS[types.DateTime].update(LOOKUPS[types.Time])

for graphql_type in list(LOOKUPS.keys()):
    if graphql_type == types.Boolean:
        continue
    LOOKUPS[graphql_type].update({
        'lt': graphql_type,
        'lte': graphql_type,
        'gt': graphql_type,
        'gte': graphql_type,
        'in': types.List(graphql_type),
        'isnull': types.Boolean,
    })
