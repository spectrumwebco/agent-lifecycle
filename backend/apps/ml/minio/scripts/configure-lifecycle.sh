set -e


MINIO_ENDPOINT=${MINIO_ENDPOINT:-"http://minio.ml-infrastructure.svc.cluster.local:9000"}
MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY:-"minioadmin"}
MINIO_SECRET_KEY=${MINIO_SECRET_KEY:-"minioadmin"}

if ! command -v mc &> /dev/null; then
  echo "MinIO client (mc) not found. Installing..."
  curl -O https://dl.min.io/client/mc/release/linux-amd64/mc
  chmod +x mc
  sudo mv mc /usr/local/bin/
fi

echo "Configuring MinIO client..."
mc alias set minio "${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}"

echo "Configuring lifecycle management for logs bucket..."
cat > /tmp/logs-lifecycle.json << EOF
{
  "Rules": [
    {
      "ID": "expire-old-logs",
      "Status": "Enabled",
      "Filter": {
        "Prefix": ""
      },
      "Expiration": {
        "Days": 30
      }
    }
  ]
}
EOF

mc ilm import minio/logs < /tmp/logs-lifecycle.json
rm /tmp/logs-lifecycle.json

echo "Configuring lifecycle management for checkpoints bucket..."
cat > /tmp/checkpoints-lifecycle.json << EOF
{
  "Rules": [
    {
      "ID": "expire-old-checkpoints",
      "Status": "Enabled",
      "Filter": {
        "Prefix": ""
      },
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 90
      },
      "Expiration": {
        "Days": 365
      }
    }
  ]
}
EOF

mc ilm import minio/checkpoints < /tmp/checkpoints-lifecycle.json
rm /tmp/checkpoints-lifecycle.json

echo "Configuring lifecycle management for model-registry bucket..."
cat > /tmp/model-registry-lifecycle.json << EOF
{
  "Rules": [
    {
      "ID": "expire-old-model-versions",
      "Status": "Enabled",
      "Filter": {
        "Prefix": ""
      },
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 180
      }
    }
  ]
}
EOF

mc ilm import minio/model-registry < /tmp/model-registry-lifecycle.json
rm /tmp/model-registry-lifecycle.json

echo "Lifecycle management configured successfully."
