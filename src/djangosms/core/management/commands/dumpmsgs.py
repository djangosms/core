import os
import pwd
import yaml

from django.core.management.base import BaseCommand
from djangosms.core.models import Incoming

class Command(BaseCommand):
    help = 'Dumps all messages into yaml format'

    def handle(self, **options):
        result = []
        for message in Incoming.objects.all().order_by('-pk'):
            result.append(
                {'uri': message.uri,
                 'time': message.time and message.time.isoformat() or None,
                 'text': message.text,
                 })

        print yaml.dump(result)
