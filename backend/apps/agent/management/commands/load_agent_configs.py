import os
from django.core.management.base import BaseCommand
from apps.agent.models import AgentConfiguration


class Command(BaseCommand):
    help = 'Load agent configurations from YAML files'

    def handle(self, *args, **options):
        self.stdout.write('Loading agent configurations from YAML files...')
        
        try:
            count = AgentConfiguration.load_from_files()
            self.stdout.write(self.style.SUCCESS(f'Successfully loaded agent configurations'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading configurations: {str(e)}'))
