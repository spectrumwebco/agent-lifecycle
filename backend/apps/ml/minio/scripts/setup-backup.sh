set -e


MINIO_ENDPOINT=${MINIO_ENDPOINT:-"http://minio.ml-infrastructure.svc.cluster.local:9000"}
MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY:-"minioadmin"}
MINIO_SECRET_KEY=${MINIO_SECRET_KEY:-"minioadmin"}
BACKUP_ENDPOINT=${BACKUP_ENDPOINT:-"http://minio-backup.ml-infrastructure.svc.cluster.local:9000"}
BACKUP_ACCESS_KEY=${BACKUP_ACCESS_KEY:-"minioadmin"}
BACKUP_SECRET_KEY=${BACKUP_SECRET_KEY:-"minioadmin"}

if ! command -v mc &> /dev/null; then
  echo "MinIO client (mc) not found. Installing..."
  curl -O https://dl.min.io/client/mc/release/linux-amd64/mc
  chmod +x mc
  sudo mv mc /usr/local/bin/
fi

echo "Configuring MinIO client..."
mc alias set minio "${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}"
mc alias set backup "${BACKUP_ENDPOINT}" "${BACKUP_ACCESS_KEY}" "${BACKUP_SECRET_KEY}"

echo "Setting up replication for model-registry bucket..."
mc replicate add minio/model-registry \
  --remote-bucket backup/model-registry-backup \
  --priority 1 \
  --arn "arn:minio:replication::backup:model-registry-backup" \
  --region "us-east-1"

echo "Setting up replication for mlflow-artifacts bucket..."
mc replicate add minio/mlflow-artifacts \
  --remote-bucket backup/mlflow-artifacts-backup \
  --priority 1 \
  --arn "arn:minio:replication::backup:mlflow-artifacts-backup" \
  --region "us-east-1"

echo "Setting up replication for training-data bucket..."
mc replicate add minio/training-data \
  --remote-bucket backup/training-data-backup \
  --priority 1 \
  --arn "arn:minio:replication::backup:training-data-backup" \
  --region "us-east-1"

echo "Setting up scheduled backups..."
cat > /tmp/minio-backup-cron << EOF
0 2 * * * mc mirror --overwrite --remove minio/model-registry backup/model-registry-backup

0 3 * * * mc mirror --overwrite --remove minio/mlflow-artifacts backup/mlflow-artifacts-backup

0 4 * * 0 mc mirror --overwrite --remove minio/training-data backup/training-data-backup

0 5 1 * * mc mirror --overwrite --remove minio/datasets backup/datasets-backup
EOF

echo "To install the cron jobs, run:"
echo "crontab /tmp/minio-backup-cron"

echo "Backup and replication configured successfully."
