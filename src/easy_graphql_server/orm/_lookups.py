"""
    This module defines the `LOOKUPS` constant, useful for defining filters on fields.

    This is currently used for Django lookups, but could be very interesting for other ORMs too.
"""


from .. import graphql_types


LOOKUPS = {

    graphql_types.Boolean: {},

    graphql_types.Int: {},

    graphql_types.Float: {},

    graphql_types.Decimal: {},

    graphql_types.String: {
        'iexact': graphql_types.String,
        'contains': graphql_types.String,
        'icontains': graphql_types.String,
        'startswith': graphql_types.String,
        'istartswith': graphql_types.String,
        'endswith': graphql_types.String,
        'iendswith': graphql_types.String,
        'regex': graphql_types.String,
        'iregex': graphql_types.String,
    },

    graphql_types.DateTime: {
        'date': graphql_types.Date,
        'time': graphql_types.Time,
    },

    graphql_types.Date: {
        'year': graphql_types.Int,
        'iso_year': graphql_types.Int,
        'quarter': graphql_types.Int,
        'month': graphql_types.Int,
        'week': graphql_types.Int,
        'iso_week_day': graphql_types.Int,
        'week_day': graphql_types.Int,
        'day': graphql_types.Int,
    },

    graphql_types.Time: {
        'hour': graphql_types.Int,
        'minute': graphql_types.Int,
        'second': graphql_types.Int,
    },

}


LOOKUPS[graphql_types.DateTime].update(LOOKUPS[graphql_types.Date])
LOOKUPS[graphql_types.DateTime].update(LOOKUPS[graphql_types.Time])

for graphql_type in list(LOOKUPS.keys()):
    if graphql_type == graphql_types.Boolean:
        continue
    LOOKUPS[graphql_type].update({
        'lt': graphql_type,
        'lte': graphql_type,
        'gt': graphql_type,
        'gte': graphql_type,
        'in': graphql_types.List(graphql_type),
        'isnull': graphql_types.Boolean,
    })
