"""
Django management command to register models and routes with the Go Framework.
"""

import logging
from django.core.management.base import BaseCommand
from apps.agent.integrations.go_framework import register_django_models, register_django_routes

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Register Django models and routes with the Go Framework'

    def handle(self, *args, **options):
        """Register Django models and routes with the Go Framework."""
        self.stdout.write('Registering Django models with Go Framework...')
        register_django_models()
        self.stdout.write(self.style.SUCCESS('Successfully registered Django models with Go Framework'))
        
        self.stdout.write('Registering Django routes with Go Framework...')
        register_django_routes()
        self.stdout.write(self.style.SUCCESS('Successfully registered Django routes with Go Framework'))
