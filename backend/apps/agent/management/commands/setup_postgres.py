"""
Django management command to set up PostgreSQL databases.

This command creates the necessary PostgreSQL databases for local development.
"""

import logging
import os
import subprocess
import time
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """Set up PostgreSQL databases for local development."""
    
    help = 'Set up PostgreSQL databases for local development'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--host',
            help='PostgreSQL host',
            default='localhost',
        )
        parser.add_argument(
            '--port',
            help='PostgreSQL port',
            default='5432',
        )
        parser.add_argument(
            '--user',
            help='PostgreSQL user',
            default='postgres',
        )
        parser.add_argument(
            '--password',
            help='PostgreSQL password',
            default='postgres',
        )
        parser.add_argument(
            '--create-databases',
            help='Create PostgreSQL databases',
            action='store_true',
            default=True,
        )
        parser.add_argument(
            '--create-users',
            help='Create PostgreSQL users',
            action='store_true',
            default=True,
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(self.style.SUCCESS('Setting up PostgreSQL databases...'))
        
        host = options['host']
        port = options['port']
        user = options['user']
        password = options['password']
        create_databases = options['create_databases']
        create_users = options['create_users']
        
        if not self._check_postgres_running(host, port, user, password):
            self.stdout.write(self.style.ERROR('❌ PostgreSQL is not running. Please start PostgreSQL first.'))
            return
        
        if create_users:
            self._create_users(host, port, user, password)
        
        if create_databases:
            self._create_databases(host, port, user, password)
        
        self.stdout.write(self.style.SUCCESS('PostgreSQL setup complete!'))
    
    def _check_postgres_running(self, host, port, user, password):
        """Check if PostgreSQL is running."""
        self.stdout.write(f"Checking if PostgreSQL is running at {host}:{port}")
        
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname='postgres'
            )
            conn.close()
            
            self.stdout.write(self.style.SUCCESS(f"✅ PostgreSQL is running at {host}:{port}"))
            return True
        except ImportError:
            self.stdout.write(self.style.WARNING("psycopg2 not installed. Install with: pip install psycopg2-binary"))
            
            try:
                env = os.environ.copy()
                env['PGPASSWORD'] = password
                
                result = subprocess.run(
                    [
                        "psql",
                        "-h", host,
                        "-p", port,
                        "-U", user,
                        "-d", "postgres",
                        "-c", "SELECT 1"
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    self.stdout.write(self.style.SUCCESS(f"✅ PostgreSQL is running at {host}:{port}"))
                    return True
                else:
                    self.stdout.write(self.style.ERROR(f"❌ PostgreSQL is not running at {host}:{port}"))
                    self.stdout.write(self.style.ERROR(f"Error: {result.stderr}"))
                    return False
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error checking PostgreSQL: {e}"))
                return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error connecting to PostgreSQL: {e}"))
            return False
    
    def _create_users(self, host, port, user, password):
        """Create PostgreSQL users."""
        self.stdout.write("Creating PostgreSQL users...")
        
        users = [
            {
                'name': 'agent_user',
                'password': 'agent_password',
                'superuser': True,
                'createdb': True,
            },
            {
                'name': 'app_user',
                'password': 'app_password',
                'superuser': False,
                'createdb': False,
            }
        ]
        
        for pg_user in users:
            self.stdout.write(f"Creating user: {pg_user['name']}")
            
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    dbname='postgres'
                )
                conn.autocommit = True
                cursor = conn.cursor()
                
                cursor.execute(f"SELECT 1 FROM pg_roles WHERE rolname = '{pg_user['name']}'")
                if cursor.fetchone():
                    self.stdout.write(self.style.WARNING(f"⚠️ User already exists: {pg_user['name']}"))
                else:
                    superuser = "SUPERUSER" if pg_user['superuser'] else "NOSUPERUSER"
                    createdb = "CREATEDB" if pg_user['createdb'] else "NOCREATEDB"
                    
                    cursor.execute(f"CREATE ROLE {pg_user['name']} WITH LOGIN PASSWORD '{pg_user['password']}' {superuser} {createdb}")
                    self.stdout.write(self.style.SUCCESS(f"✅ Created user: {pg_user['name']}"))
                
                conn.close()
            except ImportError:
                self.stdout.write(self.style.WARNING("psycopg2 not installed. Using subprocess instead."))
                
                try:
                    import os
                    env = os.environ.copy()
                    env['PGPASSWORD'] = password
                    
                    result = subprocess.run(
                        [
                            "psql",
                            "-h", host,
                            "-p", port,
                            "-U", user,
                            "-d", "postgres",
                            "-t",
                            "-c", f"SELECT 1 FROM pg_roles WHERE rolname = '{pg_user['name']}'"
                        ],
                        env=env,
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    if result.stdout.strip():
                        self.stdout.write(self.style.WARNING(f"⚠️ User already exists: {pg_user['name']}"))
                    else:
                        superuser = "SUPERUSER" if pg_user['superuser'] else "NOSUPERUSER"
                        createdb = "CREATEDB" if pg_user['createdb'] else "NOCREATEDB"
                        
                        result = subprocess.run(
                            [
                                "psql",
                                "-h", host,
                                "-p", port,
                                "-U", user,
                                "-d", "postgres",
                                "-c", f"CREATE ROLE {pg_user['name']} WITH LOGIN PASSWORD '{pg_user['password']}' {superuser} {createdb}"
                            ],
                            env=env,
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        
                        if result.returncode == 0:
                            self.stdout.write(self.style.SUCCESS(f"✅ Created user: {pg_user['name']}"))
                        else:
                            self.stdout.write(self.style.ERROR(f"❌ Error creating user: {pg_user['name']}"))
                            self.stdout.write(self.style.ERROR(f"Error: {result.stderr}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Error creating user: {pg_user['name']}"))
                    self.stdout.write(self.style.ERROR(f"Error: {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error creating user: {pg_user['name']}"))
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
    
    def _create_databases(self, host, port, user, password):
        """Create PostgreSQL databases."""
        self.stdout.write("Creating PostgreSQL databases...")
        
        databases = [
            {
                'name': 'agent_runtime',
                'owner': 'agent_user',
            },
            {
                'name': 'agent_db',
                'owner': 'agent_user',
            },
            {
                'name': 'trajectory_db',
                'owner': 'agent_user',
            },
            {
                'name': 'ml_db',
                'owner': 'agent_user',
            }
        ]
        
        for db in databases:
            self.stdout.write(f"Creating database: {db['name']}")
            
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    dbname='postgres'
                )
                conn.autocommit = True
                cursor = conn.cursor()
                
                cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db['name']}'")
                if cursor.fetchone():
                    self.stdout.write(self.style.WARNING(f"⚠️ Database already exists: {db['name']}"))
                else:
                    cursor.execute(f"CREATE DATABASE {db['name']} OWNER {db['owner']}")
                    self.stdout.write(self.style.SUCCESS(f"✅ Created database: {db['name']}"))
                
                conn.close()
            except ImportError:
                self.stdout.write(self.style.WARNING("psycopg2 not installed. Using subprocess instead."))
                
                try:
                    import os
                    env = os.environ.copy()
                    env['PGPASSWORD'] = password
                    
                    result = subprocess.run(
                        [
                            "psql",
                            "-h", host,
                            "-p", port,
                            "-U", user,
                            "-d", "postgres",
                            "-t",
                            "-c", f"SELECT 1 FROM pg_database WHERE datname = '{db['name']}'"
                        ],
                        env=env,
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    if result.stdout.strip():
                        self.stdout.write(self.style.WARNING(f"⚠️ Database already exists: {db['name']}"))
                    else:
                        result = subprocess.run(
                            [
                                "psql",
                                "-h", host,
                                "-p", port,
                                "-U", user,
                                "-d", "postgres",
                                "-c", f"CREATE DATABASE {db['name']} OWNER {db['owner']}"
                            ],
                            env=env,
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        
                        if result.returncode == 0:
                            self.stdout.write(self.style.SUCCESS(f"✅ Created database: {db['name']}"))
                        else:
                            self.stdout.write(self.style.ERROR(f"❌ Error creating database: {db['name']}"))
                            self.stdout.write(self.style.ERROR(f"Error: {result.stderr}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Error creating database: {db['name']}"))
                    self.stdout.write(self.style.ERROR(f"Error: {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error creating database: {db['name']}"))
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
