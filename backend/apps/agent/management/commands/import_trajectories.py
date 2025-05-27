"""
Management command to import trajectories from the root directory into Django.
"""

import json
import os
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.agent.trajectory_utils import trajectory_manager


class Command(BaseCommand):
    help = 'Import trajectories from the root directory into Django'

    def add_arguments(self, parser):
        parser.add_argument(
            '--trajectory-id',
            type=str,
            help='Import a specific trajectory by ID',
        )

    def handle(self, *args, **options):
        self.stdout.write('Importing trajectories from root directory...')
        
        specific_id = options.get('trajectory_id')
        
        if specific_id:
            trajectory = trajectory_manager.load_trajectory(specific_id)
            if trajectory:
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully imported trajectory {specific_id}'
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f'Trajectory {specific_id} not found'
                ))
        else:
            trajectory_ids = trajectory_manager.list_trajectories()
            
            if not trajectory_ids:
                self.stdout.write(self.style.WARNING('No trajectories found in root directory'))
                return
            
            for trajectory_id in trajectory_ids:
                trajectory = trajectory_manager.load_trajectory(trajectory_id)
                if trajectory:
                    self.stdout.write(f'Imported trajectory {trajectory_id}')
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully imported {len(trajectory_ids)} trajectories'
            ))
