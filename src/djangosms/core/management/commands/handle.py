import os
import pwd

from django.core.management.base import BaseCommand

from djangosms.core.testing import handle
from djangosms.core.logging import format_incoming

class Command(BaseCommand):
    args = 'text'
    help = 'Parses the provided text message and handles it'

    def handle(self, text, **options):
        try:
            user = os.getlogin()
        except OSError:
            user = pwd.getpwuid(os.geteuid())[0]

        message = handle(user, text)
        print format_incoming(message)
