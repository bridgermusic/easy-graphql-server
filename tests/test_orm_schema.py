import unittest

from .django.schema1 import schema


class SchemaTest(unittest.TestCase):

    def setUp(self):
        self.schema_documentation = schema.get_documentation()

    def _search_schema(self, root=None, **criteria):
        if root is None:
            root = self.schema_documentation
        if isinstance(root, list):
            for item in root:
                yield from self._search_schema(item, **criteria)
        elif isinstance(root, dict):
            if all(key in root and root[key] == value for key, value in criteria.items()):
                yield root
            for key, value in root.items():
                if isinstance(value, (list, dict)):
                    yield from self._search_schema(value, **criteria)

    def _get_from_schema(self, root=None, **criteria):
        for result in self._search_schema(root=root, **criteria):
            return result

    def _get_output_type(self, name):
        for result in self._search_schema(name=name):
            if isinstance(result.get('fields'), list):
                return result

    def _check_gender_type(self, gender_type):
        self.assertEqual(gender_type['kind'], 'ENUM')
        self.assertEqual(gender_type['name'], 'person__gender__enum_type')

    def test_enum_names(self):
        # check gender argument for create_person
        create_person = self._get_from_schema(name='create_person')
        create_person_gender_arg = self._get_from_schema(root=create_person['args'], name='gender')
        self._check_gender_type(create_person_gender_arg['type'])
        # check gender argument for update_person
        update_person = self._get_from_schema(name='update_person')
        update_person_underscore_arg = self._get_from_schema(root=update_person['args'], name='_')
        update_person_underscore_input_type = self._get_from_schema(
            kind = 'INPUT_OBJECT',
            interfaces = None,
            name = update_person_underscore_arg['type']['name'])
        update_person_gender_arg = self._get_from_schema(root=update_person_underscore_input_type, name='gender')
        self._check_gender_type(update_person_gender_arg['type'])
        # check gender argument for create_house
        create_house = self._get_from_schema(name='create_house')
        create_house_tenants_input_type = self._get_from_schema(root=create_house, name='tenants')['type']['ofType']
        create_house_owner_input_type = self._get_from_schema(root=create_house, name='owner')['type']
        for input_type_reference in (create_house_tenants_input_type, create_house_owner_input_type):
            input_type = self._get_from_schema(
                kind = 'INPUT_OBJECT',
                interfaces = None,
                name = input_type_reference['name'])
            gender = self._get_from_schema(root=input_type, name='gender')
            self._check_gender_type(gender['type'])
        # check gender output
        output_types_names = set()
        for method_name in ('person', 'people', 'create_person', 'update_person', 'delete_person'):
            method = self._get_from_schema(name=method_name)
            method_type = method['type']
            if method_type['kind'] == 'LIST':
                method_type = method_type['ofType']
            self.assertEqual(method_type['kind'], 'OBJECT')
            output_types_names.add(method_type['name'])
        self.assertEqual(len(output_types_names), 1)
        for method_name in ('house', 'houses', 'create_house', 'update_house', 'delete_house'):
            method = self._get_from_schema(name=method_name)
            method_type = method['type']
            if method_type['kind'] == 'LIST':
                method_type = method_type['ofType']
            self.assertEqual(method_type['kind'], 'OBJECT')
            method_output_type = self._get_output_type(name=method_type['name'])
            for attribute in ('owner', 'tenants'):
                method_person_output_type = self._get_from_schema(method_output_type, name=attribute)
                method_type = method_person_output_type['type']
                if method_type['kind'] == 'LIST':
                    method_type = method_type['ofType']
                self.assertEqual(method_type['kind'], 'OBJECT')
                output_types_names.add(method_type['name'])
        self.assertEqual(len(output_types_names), 3)
        for output_type_name in output_types_names:
            output_type = self._get_output_type(output_type_name)
            gender = self._get_from_schema(output_type, name='gender')
            self._check_gender_type(gender['type'])
