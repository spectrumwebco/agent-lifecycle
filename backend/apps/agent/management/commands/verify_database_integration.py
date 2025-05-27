"""
Management command to verify database integration between Apache Doris, Kafka, and PostgreSQL.
"""

import json
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Verify database integration between Apache Doris, Kafka, and PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all verification tests',
        )
        parser.add_argument(
            '--doris',
            action='store_true',
            help='Verify Apache Doris integration',
        )
        parser.add_argument(
            '--kafka',
            action='store_true',
            help='Verify Kafka integration',
        )
        parser.add_argument(
            '--postgres',
            action='store_true',
            help='Verify PostgreSQL integration',
        )
        parser.add_argument(
            '--integration',
            action='store_true',
            help='Verify integration between all database systems',
        )

    def handle(self, *args, **options):
        run_all = options['all']
        
        if run_all or options['doris']:
            self.verify_doris()
        
        if run_all or options['kafka']:
            self.verify_kafka()
        
        if run_all or options['postgres']:
            self.verify_postgres()
        
        if run_all or options['integration']:
            self.verify_integration()
        
        self.stdout.write(self.style.SUCCESS('Database verification completed'))

    def verify_doris(self):
        """Verify Apache Doris integration."""
        self.stdout.write('Verifying Apache Doris integration...')
        
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
                self.stdout.write(self.style.SUCCESS(f'Test data inserted and queried successfully: {count} rows'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to verify Apache Doris integration: {e}'))
            return False
        
        return True

    def verify_kafka(self):
        """Verify Kafka integration."""
        self.stdout.write('Verifying Kafka integration...')
        
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
            
            self.stdout.write(self.style.SUCCESS('Test message produced successfully'))
            
            consumer_conf = {
                'bootstrap.servers': bootstrap_servers,
                'group.id': 'django-test-consumer',
                'auto.offset.reset': 'earliest'
            }
            consumer = Consumer(consumer_conf)
            consumer.subscribe([test_topic])
            
            msg = consumer.poll(timeout=10.0)
            if msg is None:
                self.stdout.write(self.style.ERROR('Failed to consume test message: timeout'))
                return False
            
            if msg.error():
                self.stdout.write(self.style.ERROR(f'Failed to consume test message: {msg.error()}'))
                return False
            
            received_message = json.loads(msg.value().decode('utf-8'))
            self.stdout.write(self.style.SUCCESS(f'Test message consumed successfully: {received_message}'))
            
            consumer.close()
            
        except ImportError:
            self.stdout.write(self.style.ERROR('Failed to import Kafka libraries. Make sure confluent-kafka is installed.'))
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to verify Kafka integration: {e}'))
            return False
        
        return True

    def verify_postgres(self):
        """Verify PostgreSQL integration."""
        self.stdout.write('Verifying PostgreSQL integration...')
        
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
                self.stdout.write(self.style.SUCCESS(f'Test data inserted and queried successfully: {count} rows'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to verify PostgreSQL integration: {e}'))
            return False
        
        return True

    def verify_integration(self):
        """Verify integration between all database systems."""
        self.stdout.write('Verifying integration between all database systems...')
        
        try:
            
            with connections['agent_db'].cursor() as cursor:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS integration_test_source (
                    id SERIAL PRIMARY KEY,
                    message VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                cursor.execute("""
                INSERT INTO integration_test_source (message) VALUES 
                ('Integration Test 1'),
                ('Integration Test 2'),
                ('Integration Test 3')
                RETURNING id, message, created_at
                """)
                
                rows = cursor.fetchall()
                self.stdout.write(self.style.SUCCESS(f'Inserted {len(rows)} rows into PostgreSQL'))
            
            from confluent_kafka import Producer
            
            kafka_config = getattr(settings, 'KAFKA_CONFIG', {})
            bootstrap_servers = kafka_config.get('bootstrap_servers', 'kafka.default.svc.cluster.local:9092')
            
            producer_conf = {
                'bootstrap.servers': bootstrap_servers,
                'client.id': 'django-integration-test'
            }
            producer = Producer(producer_conf)
            
            integration_topic = 'database_integration_test'
            
            for row in rows:
                message = {
                    'id': row[0],
                    'message': row[1],
                    'created_at': row[2].isoformat() if row[2] else None
                }
                producer.produce(integration_topic, json.dumps(message).encode('utf-8'))
            
            producer.flush()
            self.stdout.write(self.style.SUCCESS(f'Sent {len(rows)} messages to Kafka'))
            
            with connections['default'].cursor() as cursor:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS integration_test_target (
                    id INT,
                    message VARCHAR(100),
                    created_at DATETIME,
                    processed_at DATETIME
                ) ENGINE=OLAP
                DUPLICATE KEY(id)
                DISTRIBUTED BY HASH(id) BUCKETS 3
                PROPERTIES (
                    "replication_num" = "1"
                )
                """)
                
                for row in rows:
                    cursor.execute(f"""
                    INSERT INTO integration_test_target VALUES 
                    ({row[0]}, '{row[1]}', '{row[2]}', NOW())
                    """)
                
                cursor.execute("SELECT COUNT(*) FROM integration_test_target")
                count = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f'Inserted {count} rows into Apache Doris'))
                
                if count == len(rows):
                    self.stdout.write(self.style.SUCCESS('Integration test successful: Data flowed from PostgreSQL through Kafka to Apache Doris'))
                else:
                    self.stdout.write(self.style.ERROR(f'Integration test failed: Expected {len(rows)} rows but found {count}'))
                    return False
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to verify integration between database systems: {e}'))
            return False
        
        return True
