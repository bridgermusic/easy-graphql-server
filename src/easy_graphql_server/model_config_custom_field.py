"""
    This module defines the `ModelConfigCustomField` class.
"""

from .operations import Operation

class ModelConfigCustomField:
    """
        Configuration of a custom field added to an exposed model.
    """

    def __init__(self, name, format, read_one=None, read_many=None,
            update_one=None, update_many=None, create_one=None, create_many=None):
        self.name = name
        self.format = format
        self.read_one = read_one
        self.read_many = read_many
        self.update_one = update_one
        self.update_many = update_many
        self.create_one = create_one
        self.create_many = create_many

    def can_perfom(self, operation):
        """
            Check if the given operation can be performed on that field
        """
        if operation == Operation.CREATE:
            return self.create_one or self.create_many
        if operation == Operation.READ:
            return self.read_one or self.read_many
        if operation == Operation.UPDATE:
            return self.update_one or self.update_many
        raise NotImplementedError()

    def perform_one_read(self, instance, authenticated_user, graphql_selection):
        """
            Fetch one value for the custom field for one instance
        """
        if self.read_one:
            return self.read_one(
                instance=instance,
                authenticated_user=authenticated_user,
                graphql_selection=graphql_selection)
        if self.read_many:
            return list(self.read_many(
                instances=[instance],
                authenticated_user=authenticated_user,
                graphql_selection=graphql_selection))[0]
        raise NotImplementedError()

    def perform_many_reads(self, instances, authenticated_user, graphql_selection):
        """
            Fetch many values for the custom field of many instance
        """
        if self.read_many:
            return self.read_many(
                instances=instances,
                authenticated_user=authenticated_user,
                graphql_selection=graphql_selection)
        if self.read_one:
            return [
                self.read_one(
                    instance=instance,
                    authenticated_user=authenticated_user,
                    graphql_selection=graphql_selection)
                for instance in instances
            ]
        raise NotImplementedError()

    def perform_one_creation(self, instance, authenticated_user, value):
        """
            Update the custom field for one instance
        """
        if self.create_one:
            return self.create_one(
                instance=instance,
                authenticated_user=authenticated_user,
                value=value)
        if self.create_many:
            return list(self.create_many(
                instances=[instance],
                authenticated_user=authenticated_user,
                value=value))[0]
        raise NotImplementedError()

    def perform_one_update(self, instance, authenticated_user, value):
        """
            Update the custom field for one instance
        """
        if self.update_one:
            return self.update_one(
                instance=instance,
                authenticated_user=authenticated_user,
                value=value)
        if self.update_many:
            return list(self.update_many(
                instances=[instance],
                authenticated_user=authenticated_user,
                value=value))[0]
        raise NotImplementedError()
