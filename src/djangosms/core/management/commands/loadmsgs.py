import yaml
import iso8601

from django.core.management.base import BaseCommand

from djangosms.core.testing import handle
from djangosms.core.logging import format_incoming

class Command(BaseCommand):
    help = 'Load messages from yaml format'

    def handle(self, path, **options):
        body = open(path).read()
        for index, entry in enumerate(yaml.load(body)):
            time = iso8601.parse_date(entry['time'])
            name, ident = entry['uri'].split('://')

            message = handle(ident, entry['text'], time=time, name=name)
            print format_incoming(message)
