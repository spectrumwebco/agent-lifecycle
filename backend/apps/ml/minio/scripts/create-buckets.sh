set -e


MINIO_ENDPOINT=${MINIO_ENDPOINT:-"http://minio.ml-infrastructure.svc.cluster.local:9000"}
MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY:-"minioadmin"}
MINIO_SECRET_KEY=${MINIO_SECRET_KEY:-"minioadmin"}

REQUIRED_BUCKETS=(
  "mlflow-artifacts"
  "model-registry"
  "training-data"
  "model-serving"
  "datasets"
  "checkpoints"
  "logs"
  "metrics"
  "backups"
)

if ! command -v mc &> /dev/null; then
  echo "MinIO client (mc) not found. Installing..."
  curl -O https://dl.min.io/client/mc/release/linux-amd64/mc
  chmod +x mc
  sudo mv mc /usr/local/bin/
fi

echo "Configuring MinIO client..."
mc alias set minio "${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}"

for bucket in "${REQUIRED_BUCKETS[@]}"; do
  echo "Creating bucket: ${bucket}"
  mc mb --ignore-existing "minio/${bucket}"
done

echo "Setting bucket policies..."

mc policy set download "minio/mlflow-artifacts"

mc policy set download "minio/model-registry"

mc policy set download "minio/training-data"

mc policy set download "minio/model-serving"

echo "Configuring versioning..."
mc version enable "minio/model-registry"
mc version enable "minio/checkpoints"

echo "All buckets created and configured successfully."
