import yaml
import iso8601
import traceback

from django.core.management.base import BaseCommand

from djangosms.core.testing import handle
from djangosms.core.logging import format_incoming

class Command(BaseCommand):
    help = 'Load messages from yaml format'

    def handle(self, path, **options):
        body = open(path).read()
        for index, entry in enumerate(yaml.load(body)):
            # parse time into naive datetime-object (UTC-local)
            time = iso8601.parse_date(entry['time']).replace(tzinfo=None)
            name, ident = entry['uri'].split('://')

            try:
                message = handle(ident, entry['text'], time=time, name=name)
            except Exception, exc:
                print traceback.format_exc(exc)
                continue
            print format_incoming(message)
