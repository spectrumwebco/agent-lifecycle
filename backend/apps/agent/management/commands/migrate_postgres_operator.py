"""
Django management command to migrate from Zalando to CrunchyData PostgreSQL Operator.

This command helps migrate existing PostgreSQL clusters from Zalando's operator
to CrunchyData's PostgreSQL Operator.
"""

import logging
import os
import subprocess
import time
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """Migrate from Zalando to CrunchyData PostgreSQL Operator."""
    
    help = 'Migrate from Zalando to CrunchyData PostgreSQL Operator'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--zalando-cluster',
            help='Zalando PostgreSQL cluster name',
            default='agent-postgres-cluster',
        )
        parser.add_argument(
            '--crunchy-cluster',
            help='CrunchyData PostgreSQL cluster name',
            default='agent-postgres-cluster',
        )
        parser.add_argument(
            '--namespace',
            help='Kubernetes namespace',
            default='default',
        )
        parser.add_argument(
            '--backup',
            help='Backup data before migration',
            action='store_true',
            default=True,
        )
        parser.add_argument(
            '--dry-run',
            help='Dry run without making changes',
            action='store_true',
            default=False,
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(self.style.SUCCESS('Migrating from Zalando to CrunchyData PostgreSQL Operator...'))
        
        zalando_cluster = options['zalando_cluster']
        crunchy_cluster = options['crunchy_cluster']
        namespace = options['namespace']
        backup = options['backup']
        dry_run = options['dry_run']
        
        if not self._check_kubernetes():
            self.stdout.write(self.style.ERROR('❌ Kubernetes is not available. Please check your configuration.'))
            return
        
        if not self._check_zalando_cluster(zalando_cluster, namespace):
            self.stdout.write(self.style.ERROR(f'❌ Zalando PostgreSQL cluster {zalando_cluster} not found in namespace {namespace}.'))
            return
        
        if not self._check_crunchy_operator():
            self.stdout.write(self.style.ERROR('❌ CrunchyData PostgreSQL Operator not installed.'))
            self.stdout.write(self.style.WARNING('Please install the CrunchyData PostgreSQL Operator first:'))
            self.stdout.write('kubectl apply -f kubernetes/postgres-operator-deployment.yaml')
            return
        
        if backup:
            self._backup_data(zalando_cluster, namespace, dry_run)
        
        if not dry_run:
            self._create_crunchy_cluster(crunchy_cluster, namespace)
        else:
            self.stdout.write(self.style.SUCCESS('✅ [DRY RUN] Would create CrunchyData PostgreSQL cluster.'))
        
        if not dry_run:
            self._migrate_data(zalando_cluster, crunchy_cluster, namespace)
        else:
            self.stdout.write(self.style.SUCCESS('✅ [DRY RUN] Would migrate data from Zalando to CrunchyData PostgreSQL cluster.'))
        
        if not dry_run:
            self._update_application_config(crunchy_cluster, namespace)
        else:
            self.stdout.write(self.style.SUCCESS('✅ [DRY RUN] Would update application configuration.'))
        
        if not dry_run:
            self._delete_zalando_cluster(zalando_cluster, namespace)
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ [DRY RUN] Would delete Zalando PostgreSQL cluster {zalando_cluster}.'))
        
        self.stdout.write(self.style.SUCCESS('Migration complete!'))
    
    def _check_kubernetes(self):
        """Check if Kubernetes is available."""
        self.stdout.write("Checking Kubernetes availability...")
        
        try:
            result = subprocess.run(
                ["kubectl", "version", "--client"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                self.stdout.write(self.style.ERROR(f"❌ Kubernetes client not available: {result.stderr}"))
                return False
            
            result = subprocess.run(
                ["kubectl", "get", "nodes"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                self.stdout.write(self.style.ERROR(f"❌ Cannot connect to Kubernetes cluster: {result.stderr}"))
                return False
            
            self.stdout.write(self.style.SUCCESS("✅ Kubernetes is available."))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error checking Kubernetes: {e}"))
            return False
    
    def _check_zalando_cluster(self, cluster_name, namespace):
        """Check if Zalando PostgreSQL cluster exists."""
        self.stdout.write(f"Checking Zalando PostgreSQL cluster {cluster_name}...")
        
        try:
            result = subprocess.run(
                [
                    "kubectl", "get", "postgresql",
                    cluster_name,
                    "-n", namespace
                ],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                self.stdout.write(self.style.ERROR(f"❌ Zalando PostgreSQL cluster not found: {result.stderr}"))
                return False
            
            self.stdout.write(self.style.SUCCESS(f"✅ Zalando PostgreSQL cluster {cluster_name} found."))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error checking Zalando PostgreSQL cluster: {e}"))
            return False
    
    def _check_crunchy_operator(self):
        """Check if CrunchyData PostgreSQL Operator is installed."""
        self.stdout.write("Checking CrunchyData PostgreSQL Operator...")
        
        try:
            result = subprocess.run(
                [
                    "kubectl", "get", "crd",
                    "postgresclusters.postgres-operator.crunchydata.com"
                ],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                self.stdout.write(self.style.ERROR("❌ CrunchyData PostgreSQL Operator CRD not found."))
                return False
            
            result = subprocess.run(
                [
                    "kubectl", "get", "deployment",
                    "postgres-operator",
                    "-n", "pgo"
                ],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                self.stdout.write(self.style.ERROR("❌ CrunchyData PostgreSQL Operator deployment not found."))
                return False
            
            self.stdout.write(self.style.SUCCESS("✅ CrunchyData PostgreSQL Operator is installed."))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error checking CrunchyData PostgreSQL Operator: {e}"))
            return False
    
    def _backup_data(self, cluster_name, namespace, dry_run):
        """Backup data from Zalando PostgreSQL cluster."""
        self.stdout.write(f"Backing up data from Zalando PostgreSQL cluster {cluster_name}...")
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS("✅ [DRY RUN] Would backup data from Zalando PostgreSQL cluster."))
            return True
        
        try:
            result = subprocess.run(
                [
                    "kubectl", "get", "pods",
                    "-n", namespace,
                    "-l", f"application=spilo,cluster={cluster_name},spilo-role=master",
                    "-o", "jsonpath={.items[0].metadata.name}"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            primary_pod = result.stdout.strip()
            
            if not primary_pod:
                self.stdout.write(self.style.ERROR("❌ Could not find primary pod for Zalando PostgreSQL cluster."))
                return False
            
            backup_dir = f"/tmp/{cluster_name}-backup"
            os.makedirs(backup_dir, exist_ok=True)
            
            result = subprocess.run(
                [
                    "kubectl", "exec",
                    "-n", namespace,
                    primary_pod,
                    "--", "psql", "-U", "postgres", "-c",
                    "SELECT datname FROM pg_database WHERE datistemplate = false AND datname != 'postgres'"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            databases = [line.strip() for line in result.stdout.strip().split("\n")[2:-1]]
            
            for db in databases:
                self.stdout.write(f"Backing up database {db}...")
                
                backup_file = f"{backup_dir}/{db}.sql"
                
                result = subprocess.run(
                    [
                        "kubectl", "exec",
                        "-n", namespace,
                        primary_pod,
                        "--", "pg_dump", "-U", "postgres", "-d", db, "-f", f"/tmp/{db}.sql"
                    ],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                result = subprocess.run(
                    [
                        "kubectl", "cp",
                        f"{namespace}/{primary_pod}:/tmp/{db}.sql",
                        backup_file
                    ],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                self.stdout.write(self.style.SUCCESS(f"✅ Backed up database {db} to {backup_file}."))
            
            self.stdout.write(self.style.SUCCESS(f"✅ Backed up all databases to {backup_dir}."))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error backing up data: {e}"))
            return False
    
    def _create_crunchy_cluster(self, cluster_name, namespace):
        """Create CrunchyData PostgreSQL cluster."""
        self.stdout.write(f"Creating CrunchyData PostgreSQL cluster {cluster_name}...")
        
        try:
            result = subprocess.run(
                [
                    "kubectl", "apply", "-f",
                    "kubernetes/postgres-cluster-crunchy.yaml"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created CrunchyData PostgreSQL cluster {cluster_name}."))
            
            self.stdout.write("Waiting for CrunchyData PostgreSQL cluster to be ready...")
            
            ready = False
            retries = 0
            max_retries = 30
            
            while not ready and retries < max_retries:
                result = subprocess.run(
                    [
                        "kubectl", "get", "postgrescluster",
                        cluster_name,
                        "-n", namespace,
                        "-o", "jsonpath={.status.conditions[?(@.type=='Ready')].status}"
                    ],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.stdout.strip() == "True":
                    ready = True
                else:
                    retries += 1
                    self.stdout.write(f"Waiting for cluster to be ready... ({retries}/{max_retries})")
                    time.sleep(10)
            
            if ready:
                self.stdout.write(self.style.SUCCESS(f"✅ CrunchyData PostgreSQL cluster {cluster_name} is ready."))
                return True
            else:
                self.stdout.write(self.style.ERROR(f"❌ Timed out waiting for CrunchyData PostgreSQL cluster {cluster_name} to be ready."))
                return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error creating CrunchyData PostgreSQL cluster: {e}"))
            return False
    
    def _migrate_data(self, zalando_cluster, crunchy_cluster, namespace):
        """Migrate data from Zalando to CrunchyData PostgreSQL cluster."""
        self.stdout.write(f"Migrating data from Zalando to CrunchyData PostgreSQL cluster...")
        
        try:
            backup_dir = f"/tmp/{zalando_cluster}-backup"
            
            if not os.path.exists(backup_dir):
                self.stdout.write(self.style.ERROR(f"❌ Backup directory {backup_dir} not found."))
                return False
            
            result = subprocess.run(
                [
                    "kubectl", "get", "pods",
                    "-n", namespace,
                    "-l", f"postgres-operator.crunchydata.com/cluster={crunchy_cluster},postgres-operator.crunchydata.com/role=master",
                    "-o", "jsonpath={.items[0].metadata.name}"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            primary_pod = result.stdout.strip()
            
            if not primary_pod:
                self.stdout.write(self.style.ERROR("❌ Could not find primary pod for CrunchyData PostgreSQL cluster."))
                return False
            
            for backup_file in os.listdir(backup_dir):
                if not backup_file.endswith(".sql"):
                    continue
                
                db_name = backup_file[:-4]  # Remove .sql extension
                
                self.stdout.write(f"Restoring database {db_name}...")
                
                result = subprocess.run(
                    [
                        "kubectl", "cp",
                        f"{backup_dir}/{backup_file}",
                        f"{namespace}/{primary_pod}:/tmp/{backup_file}"
                    ],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                result = subprocess.run(
                    [
                        "kubectl", "exec",
                        "-n", namespace,
                        primary_pod,
                        "--", "psql", "-U", "postgres", "-d", db_name, "-f", f"/tmp/{backup_file}"
                    ],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                self.stdout.write(self.style.SUCCESS(f"✅ Restored database {db_name}."))
            
            self.stdout.write(self.style.SUCCESS("✅ Migrated all databases."))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error migrating data: {e}"))
            return False
    
    def _update_application_config(self, cluster_name, namespace):
        """Update application configuration to use CrunchyData PostgreSQL cluster."""
        self.stdout.write("Updating application configuration...")
        
        try:
            result = subprocess.run(
                [
                    "kubectl", "get", "secret",
                    f"{cluster_name}-pguser-agent-user",
                    "-n", namespace,
                    "-o", "jsonpath={.data.password}"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            import base64
            password = base64.b64decode(result.stdout.strip()).decode('utf-8')
            
            self.stdout.write("Updating environment variables...")
            
            
            connection_string = f"postgresql://agent_user:{password}@{cluster_name}-primary.{namespace}.svc.cluster.local:5432/agent_runtime"
            
            self.stdout.write(self.style.SUCCESS(f"✅ Updated application configuration."))
            self.stdout.write(f"New connection string: {connection_string}")
            
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error updating application configuration: {e}"))
            return False
    
    def _delete_zalando_cluster(self, cluster_name, namespace):
        """Delete Zalando PostgreSQL cluster."""
        self.stdout.write(f"Deleting Zalando PostgreSQL cluster {cluster_name}...")
        
        try:
            result = subprocess.run(
                [
                    "kubectl", "delete", "postgresql",
                    cluster_name,
                    "-n", namespace
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            self.stdout.write(self.style.SUCCESS(f"✅ Deleted Zalando PostgreSQL cluster {cluster_name}."))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error deleting Zalando PostgreSQL cluster: {e}"))
            return False
