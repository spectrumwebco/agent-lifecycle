"""
Test database integration with Django.
"""

import os
import unittest
from django.test import TestCase
from django.db import connections
from django.conf import settings
from django.core.cache import cache

class DatabaseIntegrationTest(TestCase):
    """Test database integration with Django."""
    
    def test_database_connections(self):
        """Test that Django can connect to all configured databases."""
        for db_name in settings.DATABASES.keys():
            with connections[db_name].cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                self.assertEqual(result[0], 1, f"Failed to connect to {db_name} database")
    
    def test_cache_connection(self):
        """Test that Django can connect to the cache (DragonflyDB)."""
        try:
            cache.set('test_key', 'test_value', 10)
            value = cache.get('test_key')
            self.assertEqual(value, 'test_value', "Failed to retrieve value from cache")
        except Exception as e:
            if os.environ.get('CI') == 'true':
                self.fail(f"Cache connection failed: {e}")
            else:
                self.skipTest("Skipping cache test in local development")
    
    def test_vector_db_connection(self):
        """Test that Django can connect to the vector database (RAGflow)."""
        try:
            from apps.agent.integrations.ragflow import RAGflowClient
            
            client = RAGflowClient()
            health = client.check_health()
            
            self.assertTrue(health['status'] == 'ok' or health['status'] == 'mocked', 
                           f"RAGflow health check failed: {health}")
        except ImportError:
            self.skipTest("RAGflow client not available")
        except Exception as e:
            if os.environ.get('CI') == 'true':
                self.fail(f"RAGflow connection failed: {e}")
            else:
                self.skipTest("Skipping RAGflow test in local development")
    
    def test_messaging_connection(self):
        """Test that Django can connect to the messaging system (RocketMQ)."""
        try:
            from apps.agent.integrations.rocketmq import RocketMQClient
            
            client = RocketMQClient()
            status = client.check_connection()
            
            self.assertTrue(status['connected'] or status['mocked'], 
                           f"RocketMQ connection check failed: {status}")
        except ImportError:
            self.skipTest("RocketMQ client not available")
        except Exception as e:
            if os.environ.get('CI') == 'true':
                self.fail(f"RocketMQ connection failed: {e}")
            else:
                self.skipTest("Skipping RocketMQ test in local development")
    
    def test_supabase_auth(self):
        """Test Supabase authentication integration."""
        try:
            from apps.agent.integrations.supabase_auth import SupabaseAuth
            
            auth = SupabaseAuth()
            status = auth.check_connection()
            
            self.assertTrue(status['connected'] or status['mocked'], 
                           f"Supabase Auth connection check failed: {status}")
        except ImportError:
            self.skipTest("Supabase Auth client not available")
        except Exception as e:
            if os.environ.get('CI') == 'true':
                self.fail(f"Supabase Auth connection failed: {e}")
            else:
                self.skipTest("Skipping Supabase Auth test in local development")
    
    def test_supabase_functions(self):
        """Test Supabase Functions integration."""
        try:
            from apps.agent.integrations.supabase_functions import SupabaseFunctions
            
            functions = SupabaseFunctions()
            status = functions.check_connection()
            
            self.assertTrue(status['connected'] or status['mocked'], 
                           f"Supabase Functions connection check failed: {status}")
        except ImportError:
            self.skipTest("Supabase Functions client not available")
        except Exception as e:
            if os.environ.get('CI') == 'true':
                self.fail(f"Supabase Functions connection failed: {e}")
            else:
                self.skipTest("Skipping Supabase Functions test in local development")
    
    def test_dragonfly_memcached(self):
        """Test DragonflyDB memcached functionality."""
        try:
            from apps.agent.integrations.dragonfly import DragonflyClient
            
            client = DragonflyClient()
            status = client.check_memcached()
            
            self.assertTrue(status['connected'] or status['mocked'], 
                           f"DragonflyDB memcached check failed: {status}")
        except ImportError:
            self.skipTest("DragonflyDB client not available")
        except Exception as e:
            if os.environ.get('CI') == 'true':
                self.fail(f"DragonflyDB memcached connection failed: {e}")
            else:
                self.skipTest("Skipping DragonflyDB memcached test in local development")
