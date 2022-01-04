#!/usr/bin/env python

"""
    Keep it mind that easy_graphql_server is NOT a Django application, but a library
    (which can be used by Django applications).

    This file is only there to perform unit tests (executed from the `test` script).
    Django test application is located at `tests/schemas/django`.

    (if I knew how to move this file elsewhere, I would)
"""

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.schemas.django.settings')

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
