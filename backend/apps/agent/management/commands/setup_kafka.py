"""
Django management command to set up Apache Kafka.

This command creates the necessary Kafka topics for local development.
"""

import logging
import subprocess
import time
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """Set up Apache Kafka for local development."""
    
    help = 'Set up Apache Kafka for local development'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--bootstrap-servers',
            help='Kafka bootstrap servers',
            default='localhost:9092',
        )
        parser.add_argument(
            '--create-topics',
            help='Create Kafka topics',
            action='store_true',
            default=True,
        )
        parser.add_argument(
            '--replication-factor',
            help='Replication factor for topics',
            type=int,
            default=1,
        )
        parser.add_argument(
            '--partitions',
            help='Number of partitions for topics',
            type=int,
            default=1,
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(self.style.SUCCESS('Setting up Apache Kafka...'))
        
        bootstrap_servers = options['bootstrap_servers']
        create_topics = options['create_topics']
        replication_factor = options['replication_factor']
        partitions = options['partitions']
        
        if not self.check_kafka_running(bootstrap_servers):
            self.stdout.write(self.style.ERROR('❌ Apache Kafka is not running. Please start Kafka first.'))
            return
        
        if create_topics:
            topics = [
                'agent-events',
                'agent-commands',
                'agent-responses',
                'agent-logs',
                'trajectory-events',
                'ml-events',
                'ml-commands',
                'ml-responses',
                'ml-logs',
                'shared-state',
            ]
            
            for topic in topics:
                self.create_topic(topic, bootstrap_servers, replication_factor, partitions)
        
        self.stdout.write(self.style.SUCCESS('Apache Kafka setup complete!'))
    
    def check_kafka_running(self, bootstrap_servers):
        """Check if Kafka is running."""
        self.stdout.write(f"Checking if Apache Kafka is running at {bootstrap_servers}")
        
        try:
            try:
                from confluent_kafka.admin import AdminClient
                from confluent_kafka import KafkaException
            except ImportError:
                self.stdout.write(self.style.WARNING("confluent-kafka not installed. Install with: pip install confluent-kafka"))
                
                import socket
                host, port = bootstrap_servers.split(':')
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, int(port)))
                sock.close()
                
                if result == 0:
                    self.stdout.write(self.style.SUCCESS(f"✅ Apache Kafka is running at {bootstrap_servers}"))
                    return True
                else:
                    self.stdout.write(self.style.ERROR(f"❌ Apache Kafka is not running at {bootstrap_servers}"))
                    return False
            
            admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})
            cluster_metadata = admin_client.list_topics(timeout=5)
            
            if cluster_metadata:
                self.stdout.write(self.style.SUCCESS(f"✅ Apache Kafka is running at {bootstrap_servers}"))
                return True
            else:
                self.stdout.write(self.style.ERROR(f"❌ Apache Kafka is not running at {bootstrap_servers}"))
                return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error checking Kafka: {e}"))
            return False
    
    def create_topic(self, topic, bootstrap_servers, replication_factor, partitions):
        """Create a Kafka topic."""
        self.stdout.write(f"Creating topic: {topic}")
        
        try:
            try:
                from confluent_kafka.admin import AdminClient, NewTopic
                from confluent_kafka import KafkaException
            except ImportError:
                self.stdout.write(self.style.WARNING("confluent-kafka not installed. Install with: pip install confluent-kafka"))
                
                try:
                    result = subprocess.run(
                        [
                            "kafka-topics",
                            "--create",
                            "--topic", topic,
                            "--bootstrap-server", bootstrap_servers,
                            "--replication-factor", str(replication_factor),
                            "--partitions", str(partitions)
                        ],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    if result.returncode == 0:
                        self.stdout.write(self.style.SUCCESS(f"✅ Created topic: {topic}"))
                        return True
                    elif "already exists" in result.stderr:
                        self.stdout.write(self.style.WARNING(f"⚠️ Topic already exists: {topic}"))
                        return True
                    else:
                        self.stdout.write(self.style.ERROR(f"❌ Error creating topic: {result.stderr}"))
                        return False
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Error creating topic: {e}"))
                    return False
            
            admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})
            
            existing_topics = admin_client.list_topics(timeout=5).topics
            if topic in existing_topics:
                self.stdout.write(self.style.WARNING(f"⚠️ Topic already exists: {topic}"))
                return True
            
            new_topic = NewTopic(
                topic,
                num_partitions=partitions,
                replication_factor=replication_factor
            )
            
            result = admin_client.create_topics([new_topic])
            
            for topic_name, future in result.items():
                try:
                    future.result()  # Wait for the result
                    self.stdout.write(self.style.SUCCESS(f"✅ Created topic: {topic_name}"))
                except KafkaException as e:
                    if "already exists" in str(e):
                        self.stdout.write(self.style.WARNING(f"⚠️ Topic already exists: {topic_name}"))
                    else:
                        self.stdout.write(self.style.ERROR(f"❌ Error creating topic: {e}"))
                        return False
            
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error creating topic: {e}"))
            return False
