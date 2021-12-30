import django.db

from ..orm_model_manager import OrmModelManager, OrmModelFields, ForeignField, RelatedField
from ..operations import Operation
from .. import types
from .lookups import LOOKUPS
from .convert import to_graphql_type_from_django_field


class DjangoModelFields(OrmModelFields): # pylint: disable=R0903 # Too few public methods

    def __init__(self, orm_model):
        OrmModelFields.__init__(self, orm_model)
        # primary key
        self.primary = orm_model._meta.pk.name
        # value & foreign fields
        for field in orm_model._meta.fields:
            # is it a foreign key?
            if isinstance(field, django.db.models.fields.related.ForeignKey):
                # field to which the foreign key is referring
                related_field = field.foreign_related_fields[0]
                # value field
                self.value[field.attname] = to_graphql_type_from_django_field(related_field)
                # foreign field
                self.foreign[field.name] = ForeignField(
                    orm_model = related_field.model,
                    field_name = field.name,
                    value_field_name = field.attname)
            # if not, it is a regular value field
            else:
                # value field
                self.value[field.name] = to_graphql_type_from_django_field(field)
            # can it serve as a unique identifier?
            if field.unique:
                self.unique[field.attname] = self.value[field.attname]
        # related fields
        for related in orm_model._meta.related_objects:
            self.related[related.name] = RelatedField(
                orm_model = related.related_model,
                field_name = related.field.name,
                value_field_name = related.field.attname)


class DjangoModelManager(OrmModelManager):

    model_fields_class = DjangoModelFields

    # public methods to retrieve available filters for querying

    # pylint: disable=W0221 # Number of parameters was 1 in 'OrmModelManager.get_filters'
    def get_filters(self, mapping=None, prefix=''):
        filters = {}
        # base mapping
        if mapping is None:
            mapping = self.model.get_type_mapping(Operation.READ)
        # browse all fields
        for field_name, graphql_type in mapping.items():
            prefixed_field_name = f'{prefix}{field_name}'
            # foreign & related field
            if isinstance(graphql_type, (dict, list)):
                mapping = graphql_type[0] if isinstance(graphql_type, list) else graphql_type
                filters |= self.get_filters(mapping, f'{prefixed_field_name}__')
            # value field
            elif graphql_type in LOOKUPS:
                # basic filter (equality)
                filters[prefixed_field_name] = graphql_type
                # browse & add available lookups
                for lookup_name, lookup_graphql_type in LOOKUPS.get(graphql_type, {}).items():
                    filters[f'{prefixed_field_name}__{lookup_name}'] = lookup_graphql_type
                    # apply same filters as for integers on date/time parts
                    if (graphql_type in (types.Date, types.DateTime, types.Time)
                            and lookup_graphql_type == types.Int):
                        int_lookups = LOOKUPS[types.Int]
                        for int_lookup_name, int_lookup_graphql_type in int_lookups.items():
                            name = f'{prefixed_field_name}__{lookup_name}__{int_lookup_name}'
                            filters[name] = int_lookup_graphql_type
        # result
        return filters

    # public methods to perform queries & mutations on model instances

    def fetch_one(self, graphql_selection, **filters):
        instance = self._fetch(graphql_selection, **filters).get()
        return self._instance_to_dict(instance, graphql_selection)

    def fetch_many(self, graphql_selection, **filters):
        return [
            self._instance_to_dict(instance, graphql_selection)
            for instance
            in self._fetch(graphql_selection, **filters).all()
        ]

    def delete_one(self, graphql_selection, **filters):
        instance = self._fetch(graphql_selection, **filters).get()
        instance.delete()
        return self._instance_to_dict(instance, graphql_selection)

    # all the below methods are helpers for `fetch_one` and `fetch_many`

    def _fetch(self, graphql_selection, **filters):
        return self.build_queryset(graphql_selection).filter(**filters)

    @classmethod
    def _instance_to_dict(cls, instance, graphql_selection):
        result = {}
        for key, graphql_subselection in graphql_selection.items():
            value = getattr(instance, key)
            # value field
            if graphql_subselection is None:
                result[key] = value
            # related field
            elif type(value).__name__ == 'RelatedManager':
                result[key] = [
                    cls._instance_to_dict(child_instance, graphql_subselection)
                    for child_instance in value.all()
                ]
            # foreign field
            elif value is not None:
                result[key] = cls._instance_to_dict(value, graphql_subselection)
        return result

    def build_queryset(self, graphql_selection):
        base_queryset, only, prefetch_related, select_related = (
            self.build_queryset_parts(graphql_selection)
        )
        return (base_queryset
            .only(*only)
            .prefetch_related(*prefetch_related)
            .select_related(*select_related)
        )

    def build_queryset_parts(self, graphql_selection, field_prefix=''): # pylint: disable=R0914 # Too many local variables
        # initialize result
        base_queryset = self.orm_model.objects
        only = []
        prefetch_related = []
        select_related = []
        # browse fields in GraphQL selection
        for field_name, graphql_subselection in graphql_selection.items():
            # no subselection, this is a direct field
            if graphql_subselection is None:
                only.append(field_prefix + field_name)
            # there is a subselection, and it is a foreign key
            elif field_name in self.fields.foreign:
                foreign_field = self.fields.foreign[field_name]
                only.append(field_prefix + foreign_field.value_field_name)
                select_related.append(field_prefix + field_name)
                foreign_orm_model_manager = self.model.schema.get_model_config_from_orm_model(
                    foreign_field.orm_model).orm_model_manager
                # pylint: disable=W0612 # Unused variable '_'
                _, foreign_only, foreign_prefetch_related, foreign_select_related = (
                    foreign_orm_model_manager.build_queryset_parts(
                        graphql_subselection, f'{field_prefix}{field_name}__')
                )
                only |= foreign_only
                prefetch_related += foreign_prefetch_related
                select_related += foreign_select_related
            # there is a subselection, and it is a related field
            elif field_name in self.fields.related:
                related_field = self.fields.related[field_name]
                related_model_config = self.model.schema.get_model_config_from_orm_model(
                    related_field.orm_model)
                prefetch_related.append(
                    django.db.models.Prefetch(
                        field_name,
                        queryset = related_model_config.orm_model_manager.build_queryset(
                            graphql_subselection | {related_field.value_field_name: None})
                    )
                )
        # return resulting queryset
        return base_queryset, only, prefetch_related, select_related
