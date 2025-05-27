"""
Django management command to test database connections.

This command tests connections to all configured databases
and reports their status.
"""

import logging
from django.core.management.base import BaseCommand
from django.db import connections
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Test database connections."""
    
    help = 'Test connections to all configured databases'
    
    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(self.style.SUCCESS('Testing database connections...'))
        
        for db_name in connections:
            self.stdout.write(f"Testing connection to {db_name} database...")
            
            try:
                connection = connections[db_name]
                connection.ensure_connection()
                
                if connection.is_usable():
                    self.stdout.write(self.style.SUCCESS(f"✅ Connection to {db_name} database is working"))
                    
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT version();")
                        version = cursor.fetchone()[0]
                        self.stdout.write(f"   Database version: {version}")
                        
                        cursor.execute("SELECT current_database();")
                        db = cursor.fetchone()[0]
                        self.stdout.write(f"   Current database: {db}")
                else:
                    self.stdout.write(self.style.ERROR(f"❌ Connection to {db_name} database is not usable"))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error connecting to {db_name} database: {e}"))
        
        self.stdout.write("\nTesting Redis (DragonflyDB) connection...")
        
        try:
            import redis
            
            redis_config = getattr(settings, 'REDIS_CONFIG', {})
            
            r = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                password=redis_config.get('password', None),
                ssl=redis_config.get('ssl', False),
                socket_timeout=5
            )
            
            if r.ping():
                self.stdout.write(self.style.SUCCESS("✅ Connection to Redis (DragonflyDB) is working"))
                
                info = r.info()
                self.stdout.write(f"   Redis version: {info.get('redis_version', 'Unknown')}")
                self.stdout.write(f"   Redis mode: {info.get('redis_mode', 'Unknown')}")
                self.stdout.write(f"   Connected clients: {info.get('connected_clients', 'Unknown')}")
            else:
                self.stdout.write(self.style.ERROR("❌ Connection to Redis (DragonflyDB) failed"))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error connecting to Redis (DragonflyDB): {e}"))
        
        self.stdout.write("\nTesting RAGflow connection...")
        
        try:
            import requests
            
            vector_db_config = getattr(settings, 'VECTOR_DB_CONFIG', {})
            
            url = f"http://{vector_db_config.get('host', 'localhost')}:{vector_db_config.get('port', 8000)}/health"
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS("✅ Connection to RAGflow is working"))
                self.stdout.write(f"   Status: {response.json().get('status', 'Unknown')}")
            else:
                self.stdout.write(self.style.ERROR(f"❌ Connection to RAGflow failed with status code {response.status_code}"))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error connecting to RAGflow: {e}"))
        
        self.stdout.write("\nTesting RocketMQ connection...")
        
        try:
            import socket
            
            rocketmq_config = getattr(settings, 'ROCKETMQ_CONFIG', {})
            
            host = rocketmq_config.get('host', 'localhost')
            port = rocketmq_config.get('port', 9876)
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            
            result = s.connect_ex((host, port))
            
            if result == 0:
                self.stdout.write(self.style.SUCCESS("✅ Connection to RocketMQ is working"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ Connection to RocketMQ failed with error code {result}"))
            
            s.close()
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error connecting to RocketMQ: {e}"))
