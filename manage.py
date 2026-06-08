#!/usr/bin/env python
"""Django command-line utility for IMSO."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "imso_backend.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
