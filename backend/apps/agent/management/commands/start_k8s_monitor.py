"""
Django management command to start the Kubernetes monitor.

This command starts the Kubernetes monitor to feed events into Kafka.
"""

import logging
import time
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """Start the Kubernetes monitor."""
    
    help = 'Start the Kubernetes monitor to feed events into Kafka'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--namespace',
            help='Kubernetes namespace to monitor',
            default='default',
        )
        parser.add_argument(
            '--poll-interval',
            help='Poll interval in seconds',
            type=int,
            default=30,
        )
        parser.add_argument(
            '--resources',
            help='Comma-separated list of resources to monitor',
            default='pods,services,deployments,statefulsets,configmaps,secrets',
        )
        parser.add_argument(
            '--daemon',
            help='Run as a daemon',
            action='store_true',
            default=False,
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(self.style.SUCCESS('Starting Kubernetes monitor...'))
        
        namespace = options['namespace']
        poll_interval = options['poll_interval']
        resources = options['resources'].split(',')
        daemon = options['daemon']
        
        try:
            from apps.agent.integrations.k8s_monitor import K8sMonitor, K8sMonitorConfig
            from backend.db.integrations.kafka import KafkaClient
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'❌ Error importing required modules: {e}'))
            self.stdout.write(self.style.ERROR('Make sure the required modules are installed.'))
            return
        
        try:
            kafka_client = KafkaClient()
            
            kafka_status = kafka_client.check_connection()
            
            if not kafka_status['connected'] and not kafka_status['mocked']:
                self.stdout.write(self.style.ERROR('❌ Apache Kafka is not running.'))
                self.stdout.write(self.style.ERROR('Please start Kafka first or use mock mode.'))
                return
            
            if kafka_status['mocked']:
                self.stdout.write(self.style.WARNING('⚠️ Using mock Kafka client.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating Kafka client: {e}'))
            self.stdout.write(self.style.ERROR('Using mock Kafka client.'))
            kafka_client = None
        
        try:
            config = K8sMonitorConfig(
                namespace=namespace,
                poll_interval=poll_interval,
                resources_to_monitor=resources
            )
            
            monitor = K8sMonitor(config=config, kafka_client=kafka_client)
            
            monitor.start_monitor()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Started Kubernetes monitor for {namespace} namespace'))
            self.stdout.write(self.style.SUCCESS(f'Monitoring resources: {", ".join(resources)}'))
            self.stdout.write(self.style.SUCCESS(f'Poll interval: {poll_interval} seconds'))
            
            if daemon:
                self.stdout.write(self.style.SUCCESS('Running as a daemon. Press Ctrl+C to stop.'))
                
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    self.stdout.write(self.style.SUCCESS('Stopping Kubernetes monitor...'))
                    monitor.stop_monitor()
                    self.stdout.write(self.style.SUCCESS('Kubernetes monitor stopped.'))
            else:
                self.stdout.write(self.style.SUCCESS('Monitor started in the background.'))
                self.stdout.write(self.style.SUCCESS('Use the stop_k8s_monitor command to stop it.'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error starting Kubernetes monitor: {e}'))
            return
