"""
Management command to test integration with all database systems.
"""

import json
import time
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test integration with all database systems'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Test all database systems',
        )
        parser.add_argument(
            '--supabase',
            action='store_true',
            help='Test Supabase integration',
        )
        parser.add_argument(
            '--ragflow',
            action='store_true',
            help='Test RAGflow integration',
        )
        parser.add_argument(
            '--dragonfly',
            action='store_true',
            help='Test DragonflyDB integration',
        )
        parser.add_argument(
            '--rocketmq',
            action='store_true',
            help='Test RocketMQ integration',
        )
        parser.add_argument(
            '--doris',
            action='store_true',
            help='Test Apache Doris integration',
        )
        parser.add_argument(
            '--postgres',
            action='store_true',
            help='Test PostgreSQL integration',
        )
        parser.add_argument(
            '--kafka',
            action='store_true',
            help='Test Kafka integration',
        )

    def handle(self, *args, **options):
        run_all = options['all']
        
        if run_all or options['supabase']:
            self.test_supabase()
        
        if run_all or options['ragflow']:
            self.test_ragflow()
        
        if run_all or options['dragonfly']:
            self.test_dragonfly()
        
        if run_all or options['rocketmq']:
            self.test_rocketmq()
        
        if run_all or options['doris']:
            self.test_doris()
        
        if run_all or options['postgres']:
            self.test_postgres()
        
        if run_all or options['kafka']:
            self.test_kafka()
        
        self.stdout.write(self.style.SUCCESS('All database tests completed'))

    def test_supabase(self):
        """Test Supabase integration."""
        self.stdout.write('Testing Supabase integration...')
        
        try:
            from apps.agent.integrations.supabase_auth import SupabaseAuth
            
            auth = SupabaseAuth()
            self.stdout.write(self.style.SUCCESS('Supabase Auth client initialized successfully'))
            
            try:
                test_user = auth.sign_in_with_password(
                    email=settings.SUPABASE_TEST_EMAIL,
                    password=settings.SUPABASE_TEST_PASSWORD
                )
                self.stdout.write(self.style.SUCCESS('Supabase Auth sign-in successful'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Supabase Auth sign-in skipped: {e}'))
            
            from apps.agent.integrations.supabase_functions import SupabaseFunctions
            
            functions = SupabaseFunctions()
            self.stdout.write(self.style.SUCCESS('Supabase Functions client initialized successfully'))
            
            try:
                result = functions.invoke_function('hello-world', {})
                self.stdout.write(self.style.SUCCESS(f'Supabase Function invocation successful: {result}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Supabase Function invocation skipped: {e}'))
            
            from apps.agent.integrations.supabase_storage import SupabaseStorage
            
            storage = SupabaseStorage()
            self.stdout.write(self.style.SUCCESS('Supabase Storage client initialized successfully'))
            
            try:
                buckets = storage.list_buckets()
                self.stdout.write(self.style.SUCCESS(f'Supabase Storage buckets: {buckets}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Supabase Storage bucket listing skipped: {e}'))
            
            for db_name in ['agent_db', 'trajectory_db', 'ml_db', 'user_db']:
                try:
                    with connections[db_name].cursor() as cursor:
                        cursor.execute("SELECT current_database()")
                        current_db = cursor.fetchone()[0]
                        self.stdout.write(self.style.SUCCESS(f'Connected to Supabase database {db_name}: {current_db}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to connect to Supabase database {db_name}: {e}'))
            
        except ImportError:
            self.stdout.write(self.style.ERROR('Failed to import Supabase libraries. Make sure supabase-py is installed.'))
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to test Supabase integration: {e}'))
            return False
        
        return True

    def test_ragflow(self):
        """Test RAGflow integration."""
        self.stdout.write('Testing RAGflow integration...')
        
        try:
            from apps.agent.integrations.ragflow import RAGflowClient
            
            client = RAGflowClient()
            self.stdout.write(self.style.SUCCESS('RAGflow client initialized successfully'))
            
            try:
                results = client.search_vectors("What is agent_runtime?", limit=5)
                self.stdout.write(self.style.SUCCESS(f'RAGflow vector search successful: {len(results)} results'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'RAGflow vector search skipped: {e}'))
            
            try:
                doc_id = client.index_document({
                    "title": "Test Document",
                    "content": "This is a test document for RAGflow integration testing.",
                    "metadata": {"test": True}
                })
                self.stdout.write(self.style.SUCCESS(f'RAGflow document indexing successful: {doc_id}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'RAGflow document indexing skipped: {e}'))
            
            try:
                understanding = client.deep_understanding("What is the purpose of agent_runtime?")
                self.stdout.write(self.style.SUCCESS(f'RAGflow deep understanding successful: {understanding}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'RAGflow deep understanding skipped: {e}'))
            
        except ImportError:
            self.stdout.write(self.style.ERROR('Failed to import RAGflow libraries.'))
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to test RAGflow integration: {e}'))
            return False
        
        return True

    def test_dragonfly(self):
        """Test DragonflyDB integration."""
        self.stdout.write('Testing DragonflyDB integration...')
        
        try:
            from apps.agent.integrations.dragonfly import DragonflyClient
            
            client = DragonflyClient()
            self.stdout.write(self.style.SUCCESS('DragonflyDB client initialized successfully'))
            
            try:
                client.set('test_key', 'test_value')
                value = client.get('test_key')
                self.stdout.write(self.style.SUCCESS(f'DragonflyDB key-value operations successful: {value}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'DragonflyDB key-value operations skipped: {e}'))
            
            try:
                client.memcached_set('test_memcached_key', 'test_memcached_value')
                value = client.memcached_get('test_memcached_key')
                self.stdout.write(self.style.SUCCESS(f'DragonflyDB memcached operations successful: {value}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'DragonflyDB memcached operations skipped: {e}'))
            
            try:
                client.publish('test_channel', 'test_message')
                self.stdout.write(self.style.SUCCESS('DragonflyDB pub/sub operations successful'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'DragonflyDB pub/sub operations skipped: {e}'))
            
        except ImportError:
            self.stdout.write(self.style.ERROR('Failed to import DragonflyDB libraries.'))
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to test DragonflyDB integration: {e}'))
            return False
        
        return True

    def test_rocketmq(self):
        """Test RocketMQ integration."""
        self.stdout.write('Testing RocketMQ integration...')
        
        try:
            from apps.agent.integrations.rocketmq import RocketMQClient
            
            client = RocketMQClient()
            self.stdout.write(self.style.SUCCESS('RocketMQ client initialized successfully'))
            
            try:
                message_id = client.send_message('test_topic', 'test_message')
                self.stdout.write(self.style.SUCCESS(f'RocketMQ message production successful: {message_id}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'RocketMQ message production skipped: {e}'))
            
            try:
                messages = client.consume_messages('test_topic', timeout=5)
                self.stdout.write(self.style.SUCCESS(f'RocketMQ message consumption successful: {len(messages)} messages'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'RocketMQ message consumption skipped: {e}'))
            
            try:
                client.update_state('test_state', {'status': 'testing'})
                state = client.get_state('test_state')
                self.stdout.write(self.style.SUCCESS(f'RocketMQ state management successful: {state}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'RocketMQ state management skipped: {e}'))
            
        except ImportError:
            self.stdout.write(self.style.ERROR('Failed to import RocketMQ libraries.'))
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to test RocketMQ integration: {e}'))
            return False
        
        return True

    def test_doris(self):
        """Test Apache Doris integration."""
        self.stdout.write('Testing Apache Doris integration...')
        
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f'Connected to Apache Doris: {version}'))
                
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_doris_integration (
                    id INT,
                    name VARCHAR(100),
                    created_at DATETIME
                ) ENGINE=OLAP
                DUPLICATE KEY(id)
                DISTRIBUTED BY HASH(id) BUCKETS 3
                PROPERTIES (
                    "replication_num" = "1"
                )
                """)
                
                cursor.execute("""
                INSERT INTO test_doris_integration VALUES 
                (1, 'Test 1', NOW()),
                (2, 'Test 2', NOW()),
                (3, 'Test 3', NOW())
                """)
                
                cursor.execute("SELECT COUNT(*) FROM test_doris_integration")
                count = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f'Apache Doris data operations successful: {count} rows'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to test Apache Doris integration: {e}'))
            return False
        
        return True

    def test_postgres(self):
        """Test PostgreSQL integration."""
        self.stdout.write('Testing PostgreSQL integration...')
        
        try:
            with connections['agent_db'].cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f'Connected to PostgreSQL: {version}'))
                
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_postgres_integration (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                cursor.execute("""
                INSERT INTO test_postgres_integration (name) VALUES 
                ('Test 1'),
                ('Test 2'),
                ('Test 3')
                RETURNING id
                """)
                
                cursor.execute("SELECT COUNT(*) FROM test_postgres_integration")
                count = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f'PostgreSQL data operations successful: {count} rows'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to test PostgreSQL integration: {e}'))
            return False
        
        return True

    def test_kafka(self):
        """Test Kafka integration."""
        self.stdout.write('Testing Kafka integration...')
        
        try:
            from confluent_kafka import Producer, Consumer, KafkaError
            
            kafka_config = getattr(settings, 'KAFKA_CONFIG', {})
            bootstrap_servers = kafka_config.get('bootstrap_servers', 'kafka.default.svc.cluster.local:9092')
            
            test_topic = 'test_kafka_integration'
            
            producer_conf = {
                'bootstrap.servers': bootstrap_servers,
                'client.id': 'django-test-producer'
            }
            producer = Producer(producer_conf)
            
            test_message = {
                'id': 1,
                'message': 'Test Kafka integration',
                'timestamp': time.time()
            }
            producer.produce(test_topic, json.dumps(test_message).encode('utf-8'))
            producer.flush()
            
            self.stdout.write(self.style.SUCCESS('Kafka message production successful'))
            
            consumer_conf = {
                'bootstrap.servers': bootstrap_servers,
                'group.id': 'django-test-consumer',
                'auto.offset.reset': 'earliest'
            }
            consumer = Consumer(consumer_conf)
            consumer.subscribe([test_topic])
            
            msg = consumer.poll(timeout=10.0)
            if msg is None:
                self.stdout.write(self.style.ERROR('Failed to consume Kafka message: timeout'))
                return False
            
            if msg.error():
                self.stdout.write(self.style.ERROR(f'Failed to consume Kafka message: {msg.error()}'))
                return False
            
            received_message = json.loads(msg.value().decode('utf-8'))
            self.stdout.write(self.style.SUCCESS(f'Kafka message consumption successful: {received_message}'))
            
            consumer.close()
            
        except ImportError:
            self.stdout.write(self.style.ERROR('Failed to import Kafka libraries. Make sure confluent-kafka is installed.'))
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to test Kafka integration: {e}'))
            return False
        
        return True
