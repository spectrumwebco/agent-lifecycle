#!/bin/bash
set -e

echo "===== COMPREHENSIVE CERT-MANAGER CLEANUP ====="

# Remove Helm release if it exists
echo "Removing Helm release..."
helm uninstall cert-manager -n cert-manager 2>/dev/null || true

# Find and delete all cert-manager ClusterRoles
echo "Deleting all cert-manager ClusterRoles..."
kubectl get clusterroles | grep cert-manager | awk '{print $1}' | while read role; do
  echo "Deleting ClusterRole: $role"
  kubectl delete clusterrole "$role" --ignore-not-found
done

# Find and delete all cert-manager ClusterRoleBindings
echo "Deleting all cert-manager ClusterRoleBindings..."
kubectl get clusterrolebindings | grep cert-manager | awk '{print $1}' | while read binding; do
  echo "Deleting ClusterRoleBinding: $binding"
  kubectl delete clusterrolebinding "$binding" --ignore-not-found
done

# Find and delete all cert-manager CRDs
echo "Deleting all cert-manager CRDs..."
kubectl get crd | grep cert-manager.io | awk '{print $1}' | while read crd; do
  echo "Deleting CRD: $crd"
  kubectl delete crd "$crd" --ignore-not-found
done

# Additional roles mentioned in error messages
specific_roles=(
  "cert-manager-cluster-view"
  "cert-manager-cainjector"
  "cert-manager-controller-issuers"
  "cert-manager-controller-clusterissuers"
  "cert-manager-controller-certificates"
  "cert-manager-controller-orders"
  "cert-manager-controller-challenges"
  "cert-manager-controller-ingress-shim"
  "cert-manager-view"
  "cert-manager-edit"
  "cert-manager-webhook:webhook-requester"
  "cert-manager-controller-approve:cert-manager-io"
)

for role in "${specific_roles[@]}"; do
  echo "Ensuring ClusterRole $role is removed..."
  kubectl delete clusterrole "$role" --ignore-not-found
done

# Delete namespace as last step
echo "Deleting cert-manager namespace..."
kubectl delete namespace cert-manager --wait=false 2>/dev/null || true

echo "Waiting 10 seconds for resources to be removed..."
sleep 10

echo "===== CLEANUP COMPLETE ====="
