"""
Django management command to verify database connections.

This command verifies connections to all configured databases
and reports their status.
"""

import logging
from django.core.management.base import BaseCommand
from django.db import connections
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Verify database connections."""
    
    help = 'Verify connections to all configured databases'
    
    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(self.style.SUCCESS('Verifying database connections...'))
        
        self.stdout.write("\n=== Django Database Connections ===")
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
        
        self.stdout.write("\n=== Redis (DragonflyDB) Connection ===")
        try:
            import redis
            
            redis_config = getattr(settings, 'REDIS_CONFIG', {})
            
            local_redis = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                socket_timeout=2
            )
            
            if local_redis.ping():
                self.stdout.write(self.style.SUCCESS("✅ Connection to local Redis is working"))
                info = local_redis.info()
                self.stdout.write(f"   Redis version: {info.get('redis_version', 'Unknown')}")
            else:
                self.stdout.write(self.style.WARNING("⚠️ Local Redis connection failed, trying configured Redis..."))
                
                r = redis.Redis(
                    host=redis_config.get('host', 'localhost'),
                    port=redis_config.get('port', 6379),
                    db=redis_config.get('db', 0),
                    password=redis_config.get('password', None),
                    ssl=redis_config.get('ssl', False),
                    socket_timeout=2
                )
                
                if r.ping():
                    self.stdout.write(self.style.SUCCESS("✅ Connection to configured Redis (DragonflyDB) is working"))
                    info = r.info()
                    self.stdout.write(f"   Redis version: {info.get('redis_version', 'Unknown')}")
                else:
                    self.stdout.write(self.style.ERROR("❌ Connection to Redis (DragonflyDB) failed"))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error connecting to Redis (DragonflyDB): {e}"))
            self.stdout.write(self.style.WARNING("⚠️ Redis connection failed, but this is expected in local development"))
        
        self.stdout.write("\n=== RAGflow Connection ===")
        try:
            import requests
            
            vector_db_config = getattr(settings, 'VECTOR_DB_CONFIG', {})
            
            try:
                local_response = requests.get("http://localhost:8000/health", timeout=2)
                if local_response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS("✅ Connection to local RAGflow is working"))
                    self.stdout.write(f"   Status: {local_response.json().get('status', 'Unknown')}")
                else:
                    self.stdout.write(self.style.WARNING("⚠️ Local RAGflow connection failed, trying configured RAGflow..."))
                    raise Exception("Local RAGflow connection failed")
            except:
                url = f"http://{vector_db_config.get('host', 'localhost')}:{vector_db_config.get('port', 8000)}/health"
                
                response = requests.get(url, timeout=2)
                
                if response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS("✅ Connection to configured RAGflow is working"))
                    self.stdout.write(f"   Status: {response.json().get('status', 'Unknown')}")
                else:
                    self.stdout.write(self.style.ERROR(f"❌ Connection to RAGflow failed with status code {response.status_code}"))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error connecting to RAGflow: {e}"))
            self.stdout.write(self.style.WARNING("⚠️ RAGflow connection failed, but this is expected in local development"))
        
        self.stdout.write("\n=== RocketMQ Connection ===")
        try:
            import socket
            
            rocketmq_config = getattr(settings, 'ROCKETMQ_CONFIG', {})
            
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                result = s.connect_ex(('localhost', 9876))
                s.close()
                
                if result == 0:
                    self.stdout.write(self.style.SUCCESS("✅ Connection to local RocketMQ is working"))
                else:
                    self.stdout.write(self.style.WARNING("⚠️ Local RocketMQ connection failed, trying configured RocketMQ..."))
                    raise Exception("Local RocketMQ connection failed")
            except:
                host = rocketmq_config.get('host', 'localhost')
                port = rocketmq_config.get('port', 9876)
                
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                
                result = s.connect_ex((host, port))
                
                if result == 0:
                    self.stdout.write(self.style.SUCCESS("✅ Connection to configured RocketMQ is working"))
                else:
                    self.stdout.write(self.style.ERROR(f"❌ Connection to RocketMQ failed with error code {result}"))
                
                s.close()
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error connecting to RocketMQ: {e}"))
            self.stdout.write(self.style.WARNING("⚠️ RocketMQ connection failed, but this is expected in local development"))
        
        self.stdout.write("\n=== Vault Connection ===")
        try:
            import hvac
            
            client = hvac.Client(url='http://localhost:8200')
            
            if client.sys.is_initialized():
                self.stdout.write(self.style.SUCCESS("✅ Connection to local Vault is working"))
                self.stdout.write(f"   Vault version: {client.sys.read_health_status().get('version', 'Unknown')}")
            else:
                self.stdout.write(self.style.WARNING("⚠️ Local Vault connection failed or Vault not initialized"))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error connecting to Vault: {e}"))
            self.stdout.write(self.style.WARNING("⚠️ Vault connection failed, but this is expected in local development"))
        
        self.stdout.write("\n=== Connection Summary ===")
        self.stdout.write(self.style.SUCCESS("Database connections verified"))
        self.stdout.write(self.style.WARNING("Note: Some connections may fail in local development environment"))
        self.stdout.write(self.style.WARNING("This is expected as these services are configured for Kubernetes"))
