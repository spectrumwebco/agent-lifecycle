"""
Django management command to set up MariaDB databases.

This command creates the necessary MariaDB databases and users
for local development.
"""

import logging
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Set up MariaDB databases for local development."""
    
    help = 'Set up MariaDB databases for local development'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--root-password',
            help='MariaDB root password',
            default='',
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(self.style.SUCCESS('Setting up MariaDB databases...'))
        
        root_password = options['root_password']
        
        databases = [
            'agent_runtime',
            'agent_db',
            'trajectory_db',
            'ml_db',
        ]
        
        user = 'agent_user'
        password = 'agent_password'
        
        for db_name in databases:
            self.create_database(db_name, root_password)
        
        self.create_user(user, password, root_password)
        
        for db_name in databases:
            self.grant_privileges(user, db_name, root_password)
        
        self.stdout.write(self.style.SUCCESS('MariaDB setup complete!'))
    
    def create_database(self, db_name, root_password):
        """Create a MariaDB database."""
        self.stdout.write(f"Creating database: {db_name}")
        
        password_option = f"-p{root_password}" if root_password else ""
        
        try:
            cmd = f"mysql -u root {password_option} -e \"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\""
            subprocess.run(cmd, shell=True, check=True)
            self.stdout.write(self.style.SUCCESS(f"✅ Database {db_name} created successfully"))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to create database {db_name}: {e}"))
    
    def create_user(self, user, password, root_password):
        """Create a MariaDB user."""
        self.stdout.write(f"Creating user: {user}")
        
        password_option = f"-p{root_password}" if root_password else ""
        
        try:
            cmd = f"mysql -u root {password_option} -e \"CREATE USER IF NOT EXISTS '{user}'@'localhost' IDENTIFIED BY '{password}';\""
            subprocess.run(cmd, shell=True, check=True)
            self.stdout.write(self.style.SUCCESS(f"✅ User {user} created successfully"))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to create user {user}: {e}"))
    
    def grant_privileges(self, user, db_name, root_password):
        """Grant privileges to a user on a database."""
        self.stdout.write(f"Granting privileges on {db_name} to {user}")
        
        password_option = f"-p{root_password}" if root_password else ""
        
        try:
            cmd = f"mysql -u root {password_option} -e \"GRANT ALL PRIVILEGES ON {db_name}.* TO '{user}'@'localhost';\""
            subprocess.run(cmd, shell=True, check=True)
            self.stdout.write(self.style.SUCCESS(f"✅ Privileges granted on {db_name} to {user}"))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to grant privileges on {db_name} to {user}: {e}"))
