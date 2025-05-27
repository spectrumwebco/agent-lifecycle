"""
Django management command to stop the Kubernetes monitor.

This command stops the Kubernetes monitor.
"""

import logging
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """Stop the Kubernetes monitor."""
    
    help = 'Stop the Kubernetes monitor'
    
    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(self.style.SUCCESS('Stopping Kubernetes monitor...'))
        
        try:
            from apps.agent.integrations.k8s_monitor import K8sMonitor
            
            from django.core.cache import cache
            
            monitor_instance = cache.get('k8s_monitor_instance')
            
            if monitor_instance:
                monitor_instance.stop_monitor()
                cache.delete('k8s_monitor_instance')
                self.stdout.write(self.style.SUCCESS('✅ Kubernetes monitor stopped.'))
            else:
                self.stdout.write(self.style.WARNING('⚠️ No running Kubernetes monitor found.'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error stopping Kubernetes monitor: {e}'))
            return
